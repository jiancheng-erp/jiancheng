export const updateTotalPriceHelper = (row) => {
    if (row.inboundQuantity && row.unitPrice) {
        return (row.inboundQuantity * row.unitPrice).toFixed(3); // Ensure two decimal places
    }
    return 0;
}
