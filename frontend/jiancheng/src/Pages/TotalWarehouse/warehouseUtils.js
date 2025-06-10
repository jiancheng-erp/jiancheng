export const PAGESIZE = 30;
export const PAGESIZES = [30, 40, 50, 100];

export const getSummaries = (param) => {
    const { columns, data } = param;
    const sums = [];
    columns.forEach((column, index) => {
        if (column.property === 'detailAmount') {
            const total = data.reduce((sum, row) => {
                const value = Number(row.detailAmount);
                return sum + (isNaN(value) ? 0 : value);
            }, 0);
            sums[index] = total;
        } else {
            sums[index] = index === 0 ? '合计' : '';
        }
    });

    return sums;
}