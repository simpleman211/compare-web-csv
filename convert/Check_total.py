import pandas as pd


df = pd.read_excel('/home/ntkien/test/work/data/Pivot billing/CostManagement_Microsoft Azure_2024-08-20-1133-T1-2024.xlsx', sheet_name='Data', header=0)


import pandas as pd

# Giả sử grouped_df1 và grouped_df2 là 2 DataFrame đã được groupby
grouped_df1 = df.groupby(['ServiceName', 'ResourceId', 'ResourceGroupName']).agg({
    'CostUSD': 'sum',
}).reset_index()

grouped_df2 = df.groupby(['ServiceName', 'ResourceId']).agg({
    'CostUSD': 'sum',
}).reset_index()

# Tính tổng CostUSD cho từng DataFrame
total_sum_df1 = grouped_df1['CostUSD'].sum()
total_sum_df2 = grouped_df2['CostUSD'].sum()

print(f"Tổng CostUSD của grouped_df1: {total_sum_df1}")
print(f"Tổng CostUSD của grouped_df2: {total_sum_df2}")

# So sánh tổng
if total_sum_df1 == total_sum_df2:
    print("Tổng CostUSD của hai DataFrame là bằng nhau.")
else:
    print("Tổng CostUSD của hai DataFrame là khác nhau.")

# So sánh chi tiết từng hàng
comparison_df = grouped_df1.merge(grouped_df2, on='ResourceId', how='outer', suffixes=('_df1', '_df2'))
comparison_df['Difference'] = comparison_df['CostUSD_df1'] - comparison_df['CostUSD_df2']

print("So sánh chi tiết:")
print(comparison_df)
