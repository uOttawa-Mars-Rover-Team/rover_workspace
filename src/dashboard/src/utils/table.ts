/**
 * Helper function for sorting string values in tables
 *
 * @param key Data object key to be sorted at
 * @returns Table sorter function
 */
export const stringColumnSorter = (key: string) => {
  return (a: { [key: string]: string }, b: { [key: string]: string }) =>
    a[key].toLowerCase().localeCompare(b[key].toLowerCase());
};
