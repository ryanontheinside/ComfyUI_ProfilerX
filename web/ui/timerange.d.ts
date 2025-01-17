export interface TimeRangeOption {
    value: string;
    label: string;
}
export interface TimeRangeSelector {
    container: HTMLElement;
    select: HTMLSelectElement;
}
export declare function createTimeRangeSelector(): TimeRangeSelector;
export declare function filterHistoryByTimeRange(history: any[], timeRange: string): any[];
