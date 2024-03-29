import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score 
import csv

# Read each CSV file in dir "path/to/root_dir"
directory = "/Users/essen/Desktop/MTK_experiment/Performance-Prediction-and-Scheduling-on-Heterogeneous-CPUs/benchmark_data/pixel4XL"
dfs = []

for file in Path(directory).glob("**/*.csv"):
    dfs.append(pd.read_csv(file))
# Put the dataframes to a single dataframe
df = pd.concat(dfs)

PMU_list = dfs[0]['event'][0:150]
PMU_num = len(PMU_list)
frequency_num = 3
cluster_num = (int)((len(dfs[0])/frequency_num)/PMU_num)

def convert_float(num):
  b = [float(i.replace(",","")) for i in num]
  return b

def r(x, y):
    x = np.array(x)
    y = np.array(y)
    xm = x.mean()
    ym = y.mean()
    numerator = np.sum(((x - xm) * (y - ym)))
    denominator = np.sqrt(np.sum((x - xm) ** 2)) * np.sqrt(np.sum((y - ym) ** 2))
    if denominator == 0 :
        return 0
    else:
        return numerator / denominator 

def generate_PMU_R (cluster,frequency):
    PMU_R = []
    pmu_c = (cluster*frequency_num+frequency)*PMU_num

    for i in range(PMU_num):
      count = (convert_float(df['count'][i + pmu_c]))
      time = (df['time'][i + pmu_c])
      PMU_R.append(r(count,time))
    return PMU_R

def PMU_selection_by_each_freq(cluster_r,r_value):
  PMU_select =[]
  cluster_r_sort = sorted(cluster_r)

  for i in cluster_r_sort[PMU_num-6:PMU_num]:
    if abs(i) >= r_value:
      PMU_select.append(PMU_list[cluster_r.index(i)])

  return PMU_select

def print_PMU_by_each_freq():
  R_value = 0.99
  CPU = []
  frequency = []
  PMU_selection = []
  for i in range(cluster_num):
    for j in range(frequency_num):
      CPU.append(dfs[0]['setup core'][PMU_num*cluster_num*i])
      frequency.append(dfs[0]['frequency'][PMU_num*j])
      print('CPU:',dfs[0]['setup core'][PMU_num*cluster_num*i],'Frequency:',dfs[0]['frequency'][PMU_num*j])
      print('PMU list: ',PMU_list)
      PMU_selection = PMU_selection+PMU_selection_by_each_freq(generate_PMU_R(i,j),R_value)
  result = list(dict.fromkeys(PMU_selection))
  return result


def train_dataset(cluster,frequency,selection_list):
  train_data ={}
  idx = cluster*PMU_num
  
  for pmu in selection_list:
    count = []
    for t in dfs:
      count.append(t['count'][list(PMU_list).index(pmu)+idx+frequency*len(PMU_list)].replace(',',''))
    train_data[pmu] = np.array(count)
  time = []
  for t in dfs:
    time.append( t['time'][idx+frequency*len(PMU_list)])
  train_data['time'] = np.array(time)
  return  pd.DataFrame(train_data)


def train_model(cluster,frequency,R_value):
  selection_list = PMU_selection_by_each_freq(generate_PMU_R(cluster,frequency),R_value)
  data = train_dataset(cluster,frequency,selection_list)

  y = data.iloc[:, len(selection_list)]
  X = data.iloc[:, 0:len(selection_list)]
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = 0)

  regressor = LinearRegression()
  model=regressor.fit(X_train, y_train)

  y_predict = regressor.predict(X_test)
  score1=r2_score(y_test,y_predict)
  
  diff_ratio = 0
  y_test = list(y_test)
  for i in range(len(y_predict)):
    diff_ratio = diff_ratio + abs((y_predict[i]-y_test[i])/y_test[i])
    # print("predict time:", y_predict[i],"real time:", y_test[i])
  diff_ratio = 100*diff_ratio / len(y_predict)

  Validation_R=r2_score(y_test,y_predict)

  # print("model.intercept_:",model.intercept_)
  # print("model.coef_:",model.coef_)

  # print("R:",model.score(X, y))
  # print("Validation R: ",score1)
  return Validation_R, diff_ratio


def print_train_model():
  R_value = 0.95
  CPU = []
  frequency = []
  with open('/Users/essen/Desktop/MTK_experiment/Performance-Prediction-and-Scheduling-on-Heterogeneous-CPUs/result/freq/freq_pmu_4XL.csv', 'w', newline='') as csvfile:
# 建立 CSV 檔寫入器
    writer = csv.writer(csvfile)
  # 寫入一列資料
    writer.writerow(['Cluster (CPU)','Frequency', 'PMU 1', 'PMU2','PMU 3','PMU 4','PMU 5','PMU 6','Validation R','Different Ratio'])


    for i in range(cluster_num):
      for j in range(frequency_num):
        CPU.append(dfs[0]['setup core'][PMU_num*frequency_num*i])
        frequency.append(dfs[0]['frequency'][PMU_num*j])
        PMU_selection = PMU_selection_by_each_freq(generate_PMU_R(i,j),R_value)
        print('CPU:',dfs[0]['setup core'][PMU_num*frequency_num*i],'Frequency:',dfs[0]['frequency'][PMU_num*j],'PMU_list:',PMU_selection)
        row = [' ']*9
        row[0] = (dfs[0]['setup core'][PMU_num*frequency_num*i])
        row[1] = (dfs[0]['frequency'][PMU_num*j])
        row[2:1+len(PMU_selection)] = PMU_selection

        Validation_R, diff_ratio= train_model(i,j,R_value)
        print('R: ',Validation_R,"Different Ratio: ",diff_ratio,"%")
        row[8] = Validation_R
        row[9] = str(diff_ratio)+'%'
        writer.writerow(row)




def main():
  print_train_model()

if __name__ == "__main__":
    main()