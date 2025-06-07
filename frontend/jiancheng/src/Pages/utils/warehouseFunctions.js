import Decimal from "decimal.js";
export const updateTotalPriceHelper = (row) => {
    if (row.inboundQuantity && row.unitPrice) {
        let result = new Decimal(row.inboundQuantity).times(new Decimal(row.unitPrice));
        return result.toDecimalPlaces(4).toNumber(); // Ensure three decimal places
    }
    return 0;
}

export const updateTotalPriceHelperForOutbound = (row) => {
    if (row.outboundQuantity && row.unitPrice) {
        let result = new Decimal(row.outboundQuantity).times(new Decimal(row.unitPrice));
        return result.toDecimalPlaces(4).toNumber(); // Ensure three decimal places
    }
    return 0;
}
