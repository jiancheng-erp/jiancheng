# maintenance_tasks.py
import pandas as pd
from datetime import datetime
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import exists, text, inspect
import re

# 你的 models 全部已在 models.py 中
from models import (
    db,
    Supplier, Material, SPUMaterial,
    BomItem, CraftSheetItem, ProductionInstructionItem,
    PurchaseOrderItem, AssetsPurchaseOrderItem,
    InboundRecord, OutboundRecord, TotalPurchaseOrder,
    PurchaseDivideOrder, AccountingPayableAccount, AccountingPayeePayer, AccountingForeignAccountEvent,  # 若模型不存在也没关系，仅用于列检测/可选更新 # 有 supplier_id
)

# ========== 可配置：含有 supplier_id 的业务表 ==========
SUPPLIER_FK_TABLES = [
    (InboundRecord, InboundRecord.supplier_id),
    (OutboundRecord, OutboundRecord.supplier_id),
    (TotalPurchaseOrder, TotalPurchaseOrder.supplier_id),
    # 有其它含 supplier_id 的表就继续加
]

# ========== 可配置：含有 material_id 的业务表 ==========
MATERIAL_FK_TABLES = [
    (BomItem, BomItem.material_id),
    (CraftSheetItem, CraftSheetItem.material_id),
    (ProductionInstructionItem, ProductionInstructionItem.material_id),
    (PurchaseOrderItem, PurchaseOrderItem.material_id),
    (AssetsPurchaseOrderItem, AssetsPurchaseOrderItem.material_id),
    (SPUMaterial, SPUMaterial.material_id),
    # 有其它含 material_id 的表就继续加
]

def _table_has_column(session: Session, table_name: str, column_name: str) -> bool:
    """
    安全检查指定表是否存在某列。
    - 优先使用 session.get_bind() 获取当前事务的 Engine
    - 回退到 db.engine
    """
    try:
        bind = None
        # SQLAlchemy 1.4/2.0 推荐：
        if hasattr(session, "get_bind"):
            bind = session.get_bind()
        # 回退
        if bind is None and hasattr(db, "engine"):
            bind = db.engine
        if bind is None:
            return False  # 再无可用 Engine，直接返回 False，避免 NoInspectionAvailable

        insp = inspect(bind)
        cols = [c["name"] for c in insp.get_columns(table_name)]
        return column_name in cols
    except Exception:
        return False
def _update_pdo_rid_suffix(session: Session, old_sid: int, new_sid: int, dry_run: bool, log):
    """
    将 purchase_divide_order.purchase_divide_order_rid 的末4位（供应商ID编码）
    从 old_sid 的后四位替换为 new_sid 的后四位。

    规则：
    - 仅当 RID 的“最后4位都是数字且等于 old_sid % 10000 的零填充形式”时才替换；
    - 目标 new_rid 若已存在（唯一约束），自动在末尾追加“-M1/-M2/...”消歧。
    """
    old_tail = f"{old_sid % 10000:04d}"
    new_tail = f"{new_sid % 10000:04d}"

    # 先粗筛：末尾 LIKE '%dddd'
    candidates = (
        session.query(PurchaseDivideOrder)
        .filter(PurchaseDivideOrder.purchase_divide_order_rid.like(f"%{old_tail}"))
        .all()
    )
    changed = 0
    for row in candidates:
        rid = row.purchase_divide_order_rid or ""
        # 严格判断“末四位就是 old_tail 且都是数字”
        if not re.match(rf"^.*\d{{4}}$", rid):
            continue
        if not rid.endswith(old_tail):
            continue

        base = rid[:-4]  # 去掉末四位
        new_rid = base + new_tail

        # 唯一性预检查；若冲突，追加 -M{n}
        if session.query(
            exists().where(PurchaseDivideOrder.purchase_divide_order_rid == new_rid)
        ).scalar():
            n = 1
            candidate = f"{new_rid}-M{n}"
            while session.query(
                exists().where(PurchaseDivideOrder.purchase_divide_order_rid == candidate)
            ).scalar():
                n += 1
                candidate = f"{new_rid}-M{n}"
            new_rid = candidate

        log(f"[PDO.RID] {rid}  →  {new_rid}")
        changed += 1
        if not dry_run:
            row.purchase_divide_order_rid = new_rid

    if changed:
        log(f"[PDO.RID] 更新完成：{changed} 条受影响")
def _has_supplier_fk_refs(session: Session, supplier_id: int) -> bool:
    for model, col in SUPPLIER_FK_TABLES:
        if session.query(model).filter(col == supplier_id).limit(1).count():
            return True
    return False
def _read_mapping(xlsx_path: str):
    """读取Excel（A=id, B=旧名, C=新名），返回 [(old, new), ...]，过滤空白与相同名。"""
    df = pd.read_excel(xlsx_path, header=None, usecols=[0, 1, 2])
    df.columns = ["id", "old", "new"]
    df = df.fillna("")
    pairs = []
    for _, r in df.iterrows():
        old = str(r["old"]).strip()
        new = str(r["new"]).strip()
        if old and new and old != new:
            pairs.append((old, new))
    return pairs

def _choose_canonical_supplier(session: Session, target_name: str, supplier_ids: list[int]) -> Supplier:
    """选择规范供应商（同名里 id 最小；若同名不存在，则整个组 id 最小）。"""
    same = session.query(Supplier).filter(
        Supplier.supplier_name == target_name,
        Supplier.supplier_id.in_(supplier_ids)
    ).all()
    if same:
        return sorted(same, key=lambda s: s.supplier_id)[0]
    all_sup = session.query(Supplier).filter(Supplier.supplier_id.in_(supplier_ids)).all()
    return sorted(all_sup, key=lambda s: s.supplier_id)[0]

def _rebind_material_fk(session: Session, old_mid: int, new_mid: int, dry_run: bool, log):
    """把所有 material_id 外键从 old_mid 指向 new_mid，并删除旧材料。"""
    if old_mid == new_mid:
        return
    for model, col in MATERIAL_FK_TABLES:
        q = session.query(model).filter(col == old_mid)
        cnt = q.count()
        if cnt:
            log(f"[MaterialFK] {model.__tablename__}.{col.key}: {cnt} rows {old_mid} → {new_mid}")
            if not dry_run:
                q.update({col: new_mid}, synchronize_session=False)

    if not dry_run:
        # 删除旧材料（若还有遗漏外键，会抛错；把漏掉的表补进 MATERIAL_FK_TABLES）
        session.query(Material).filter(Material.material_id == old_mid).delete()
def _merge_accounting_side(session: Session, old_name: str, new_name: str, dry_run: bool, log):
    """
    将与供应商名对应的账务主体合并：
      - accounting_payable_transaction.payee_name: old → new（若列存在）
      - accounting_payee_payer: 以 new_name 为规范，选最小 payee_id 为 canonical
      - accounting_foreign_account_event.payable_payee_account_id: 指向 canonical
      - accounting_payable_account: 同币种(account_unit_id)余额相加，保留/或迁移到 canonical，再删除多余账户与多余 payee
    """

    # 0) 交易表(payable_transaction)中按名称改名（如果存在 payee_name 列）
    if _table_has_column(session, "accounting_payable_transaction", "payee_name"):
        log(f"[ACC.TXN] payee_name: '{old_name}' → '{new_name}'")
        if not dry_run:
            session.execute(
                text("""
                    UPDATE accounting_payable_transaction
                       SET payee_name = :new_name
                     WHERE payee_name = :old_name
                """),
                {"new_name": new_name, "old_name": old_name}
            )

    # 1) 找到所有同名 payee（旧名 + 现有新名）
    candidates: list[AccountingPayeePayer] = session.query(AccountingPayeePayer)\
        .filter(AccountingPayeePayer.payee_name.in_([old_name, new_name]))\
        .all()
    if not candidates:
        # 若没有任何账务主体，仅需处理交易表改名即可
        return

    # 2) 选择规范 payee（优先已有 new_name，取 payee_id 最小；否则全体最小，并将其重命名为 new_name）
    same_new = [p for p in candidates if p.payee_name == new_name]
    if same_new:
        canonical = sorted(same_new, key=lambda x: x.payee_id)[0]
    else:
        canonical = sorted(candidates, key=lambda x: x.payee_id)[0]
        if canonical.payee_name != new_name:
            log(f"[ACC.PAYEE] Rename canonical payee_id={canonical.payee_id} '{canonical.payee_name}' → '{new_name}'")
            if not dry_run:
                canonical.payee_name = new_name
                session.flush()

    canonical_id = canonical.payee_id

    # 3) 其余 payee 并入
    others = [p for p in candidates if p.payee_id != canonical_id]
    for p in sorted(others, key=lambda x: x.payee_id):
        pid = p.payee_id
        log(f"[ACC.PAYEE] Merge payee_id={pid} ('{p.payee_name}') → payee_id={canonical_id} ('{new_name}')")

        # 3.1) 重定向外键：foreign_account_event.payable_payee_account_id
        q_evt = session.query(AccountingForeignAccountEvent).filter(
            AccountingForeignAccountEvent.payable_payee_account_id == pid
        )
        cnt_evt = q_evt.count()
        if cnt_evt:
            log(f"  [ACC.FAE] payable_payee_account_id: {cnt_evt} rows {pid} → {canonical_id}")
            if not dry_run:
                q_evt.update(
                    {AccountingForeignAccountEvent.payable_payee_account_id: canonical_id},
                    synchronize_session=False
                )

        # 3.2) 合并应付账户：同币种余额相加
        old_accounts: list[AccountingPayableAccount] = session.query(AccountingPayableAccount)\
            .filter(AccountingPayableAccount.account_owner_id == pid)\
            .all()

        if old_accounts:
            # 拿到 canonical 现有账户，按币种建索引
            canon_accounts = session.query(AccountingPayableAccount)\
                .filter(AccountingPayableAccount.account_owner_id == canonical_id)\
                .all()
            canon_by_unit = {}
            for a in canon_accounts:
                canon_by_unit.setdefault(a.account_unit_id, []).append(a)

            for oa in old_accounts:
                unit = oa.account_unit_id
                # 规范侧此币种是否已有账户？
                target = None
                if unit in canon_by_unit and canon_by_unit[unit]:
                    target = canon_by_unit[unit][0]  # 取第一个作为聚合账户

                if target:
                    # 相加余额 → 删除旧账户
                    log(f"  [ACC.ACCT] unit={unit}: add {oa.account_payable_balance} → acct_id={target.account_id}; delete acct_id={oa.account_id}")
                    if not dry_run:
                        # 累加余额
                        target.account_payable_balance = (target.account_payable_balance or 0) + (oa.account_payable_balance or 0)
                        session.delete(oa)
                else:
                    # 规范侧无该币种账户 → 迁移所有权
                    log(f"  [ACC.ACCT] unit={unit}: move owner {pid} → {canonical_id} (keep acct_id={oa.account_id})")
                    if not dry_run:
                        oa.account_owner_id = canonical_id
                        session.flush()

        # 3.3) 删除被并入的 payee
        if not dry_run:
            session.delete(p)
def _merge_accounting_side(session: Session, old_name: str, new_name: str, dry_run: bool, log):
    """
    将与供应商名对应的账务主体合并：
      - accounting_payable_transaction.payee_name: old → new（若列存在）
      - accounting_payee_payer: 以 new_name 为规范，选最小 payee_id 为 canonical
      - accounting_foreign_account_event.payable_payee_account_id: 指向 canonical
      - accounting_payable_account: 同币种(account_unit_id)余额相加，保留/或迁移到 canonical，再删除多余账户与多余 payee
    """

    # 0) 交易表(payable_transaction)中按名称改名（如果存在 payee_name 列）
    if _table_has_column(session, "accounting_payable_transaction", "payee_name"):
        log(f"[ACC.TXN] payee_name: '{old_name}' → '{new_name}'")
        if not dry_run:
            session.execute(
                text("""
                    UPDATE accounting_payable_transaction
                       SET payee_name = :new_name
                     WHERE payee_name = :old_name
                """),
                {"new_name": new_name, "old_name": old_name}
            )

    # 1) 找到所有同名 payee（旧名 + 现有新名）
    candidates: list[AccountingPayeePayer] = session.query(AccountingPayeePayer)\
        .filter(AccountingPayeePayer.payee_name.in_([old_name, new_name]))\
        .all()
    if not candidates:
        # 若没有任何账务主体，仅需处理交易表改名即可
        return

    # 2) 选择规范 payee（优先已有 new_name，取 payee_id 最小；否则全体最小，并将其重命名为 new_name）
    same_new = [p for p in candidates if p.payee_name == new_name]
    if same_new:
        canonical = sorted(same_new, key=lambda x: x.payee_id)[0]
    else:
        canonical = sorted(candidates, key=lambda x: x.payee_id)[0]
        if canonical.payee_name != new_name:
            log(f"[ACC.PAYEE] Rename canonical payee_id={canonical.payee_id} '{canonical.payee_name}' → '{new_name}'")
            if not dry_run:
                canonical.payee_name = new_name
                session.flush()

    canonical_id = canonical.payee_id

    # 3) 其余 payee 并入
    others = [p for p in candidates if p.payee_id != canonical_id]
    for p in sorted(others, key=lambda x: x.payee_id):
        pid = p.payee_id
        log(f"[ACC.PAYEE] Merge payee_id={pid} ('{p.payee_name}') → payee_id={canonical_id} ('{new_name}')")

        # 3.1) 重定向外键：foreign_account_event.payable_payee_account_id
        q_evt = session.query(AccountingForeignAccountEvent).filter(
            AccountingForeignAccountEvent.payable_payee_account_id == pid
        )
        cnt_evt = q_evt.count()
        if cnt_evt:
            log(f"  [ACC.FAE] payable_payee_account_id: {cnt_evt} rows {pid} → {canonical_id}")
            if not dry_run:
                q_evt.update(
                    {AccountingForeignAccountEvent.payable_payee_account_id: canonical_id},
                    synchronize_session=False
                )

        # 3.2) 合并应付账户：同币种余额相加
        old_accounts: list[AccountingPayableAccount] = session.query(AccountingPayableAccount)\
            .filter(AccountingPayableAccount.account_owner_id == pid)\
            .all()

        if old_accounts:
            # 拿到 canonical 现有账户，按币种建索引
            canon_accounts = session.query(AccountingPayableAccount)\
                .filter(AccountingPayableAccount.account_owner_id == canonical_id)\
                .all()
            canon_by_unit = {}
            for a in canon_accounts:
                canon_by_unit.setdefault(a.account_unit_id, []).append(a)

            for oa in old_accounts:
                unit = oa.account_unit_id
                # 规范侧此币种是否已有账户？
                target = None
                if unit in canon_by_unit and canon_by_unit[unit]:
                    target = canon_by_unit[unit][0]  # 取第一个作为聚合账户

                if target:
                    # 相加余额 → 删除旧账户
                    log(f"  [ACC.ACCT] unit={unit}: add {oa.account_payable_balance} → acct_id={target.account_id}; delete acct_id={oa.account_id}")
                    if not dry_run:
                        # 累加余额
                        target.account_payable_balance = (target.account_payable_balance or 0) + (oa.account_payable_balance or 0)
                        session.delete(oa)
                else:
                    # 规范侧无该币种账户 → 迁移所有权
                    log(f"  [ACC.ACCT] unit={unit}: move owner {pid} → {canonical_id} (keep acct_id={oa.account_id})")
                    if not dry_run:
                        oa.account_owner_id = canonical_id
                        session.flush()

        # 3.3) 删除被并入的 payee
        if not dry_run:
            session.delete(p)



def merge_suppliers_from_excel(app, db, xlsx_path: str, dry_run: bool = True):
    def log(msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    with app.app_context():
        session: Session = db.session

        pairs = _read_mapping(xlsx_path)
        if not pairs:
            log("Excel 未读取到有效映射（B列旧名 / C列新名），已退出。")
            return

        old_to_new = {}
        for old, new in pairs:
            old_to_new[old] = new

        old_names = set(old_to_new.keys())
        new_names = set(old_to_new.values())

        old_suppliers = session.query(Supplier).filter(
            Supplier.supplier_name.in_(list(old_names))
        ).all()
        existing_new_suppliers = session.query(Supplier).filter(
            Supplier.supplier_name.in_(list(new_names))
        ).all()

        from collections import defaultdict
        name_to_ids = defaultdict(list)
        for s in old_suppliers:
            name_to_ids[old_to_new[s.supplier_name]].append(s.supplier_id)
        for s in existing_new_suppliers:
            name_to_ids[s.supplier_name].append(s.supplier_id)

        for k in list(name_to_ids.keys()):
            name_to_ids[k] = sorted(set(name_to_ids[k]))

        try:
            if dry_run:
                log("==== DRY RUN 开始（不提交）====")
            else:
                log("==== 执行开始 ====")

            # —— 逐个“新名”组处理
            for target_name, sids in list(name_to_ids.items()):
                if not sids:
                    continue

                # 1) “新名不存在”的判定
                target_exists = session.query(Supplier).filter(
                    Supplier.supplier_name == target_name
                ).limit(1).count() > 0

                # 2) 若新名不存在：先删本组中“无材料（且可选无引用）”的供应商
                if not target_exists:
                    remaining_sids = []
                    for sid in sids:
                        mat_cnt = session.query(Material).filter(
                            Material.material_supplier == sid
                        ).count()

                        if mat_cnt == 0:
                            # 可选更安全：若仍有其它业务表引用，则不删
                            if _has_supplier_fk_refs(session, sid):
                                log(f"[Supplier] supplier_id={sid} 无材料但仍有业务引用，保留以避免外键问题。")
                                remaining_sids.append(sid)
                                continue
                            _merge_accounting_side(session, old_name=session.get(Supplier, sid).supplier_name, new_name=target_name, dry_run=dry_run, log=log)

                            log(f"[Supplier] 新名'{target_name}'不存在，supplier_id={sid} 无材料且无引用 → 删除")
                            if not dry_run:
                                sup = session.get(Supplier, sid)
                                if sup:
                                    session.delete(sup)
                        else:
                            remaining_sids.append(sid)

                    # 刷新组成员
                    sids = remaining_sids
                    name_to_ids[target_name] = sids

                    # 若删完之后这组为空：无需再创建/改名，跳过
                    if not sids:
                        log(f"[Group] 目标新名 '{target_name}' 最终无待合并供应商，跳过。")
                        continue

                # 3) 走标准“改名+合并”流程
                _merge_supplier_group(session, target_name, sids, dry_run, log)

            if dry_run:
                session.rollback()
                log("==== DRY RUN 结束（已回滚，无持久化）====")
            else:
                session.commit()
                log("==== 执行完成，已提交 ====")

        except Exception as e:
            session.rollback()
            log(f"发生异常，已回滚：{e}")
            raise
