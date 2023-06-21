/**
 * Helper funtion for sorting string values in tables
 * 
 * @param key Data object key to be sorted at
 * @returns Table sorter function
 */
export const stringColumnSorter = (key: string) => {
    return (a: any, b: any) => a[key].toLowerCase().localeCompare(b[key].toLowerCase())
}