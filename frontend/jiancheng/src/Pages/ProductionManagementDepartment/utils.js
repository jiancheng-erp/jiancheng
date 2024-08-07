import * as XLSX from 'xlsx';
import { saveAs } from 'file-saver';

export const handleRowClick = (row) => {
    let url = ""
    const queryString = new URLSearchParams(row).toString();
    if (row.statusId === 20) {
        url = `${window.location.origin}/fabriccutting/pricereport?${queryString}`;
    } else if (row.statusId === 23) {
        url = `${window.location.origin}/fabriccutting/ordershoelist?${queryString}`;
    }
    if (url) {
        window.open(url, '_blank');
    }
}


export function exportTableToExcel(data, columns, filename = 'table.xlsx') {
    const headers = columns.map(col => col.label);
    const keys = columns.map(col => col.prop);
    const formattedData = data.map(row => {
        const formattedRow = {};
        keys.forEach(key => {
            formattedRow[key] = row[key];
        });
        return formattedRow;
    });
    const ws = XLSX.utils.json_to_sheet(formattedData, { header: keys });
    XLSX.utils.sheet_add_aoa(ws, [headers], { origin: 'A1' });
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    saveAs(new Blob([wbout], { type: 'application/octet-stream' }), filename);
}
