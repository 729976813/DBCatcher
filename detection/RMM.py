from utils import util
import numpy as np
import pandas as pd
import math
from detection import config


def cacualte_cs_queue(x, y, s):
    assert len(x) == len(y)
    assert isinstance(s, int)
    length_ = len(x)
    pow_x = 0
    pow_y = 0
    ccs = 0
    smallest_x = min(x)
    biggest_x = max(x)
    smallest_y = min(y)
    biggest_y = max(y)
    if biggest_x == smallest_x or biggest_y == smallest_y:
        if biggest_x == smallest_x and biggest_y == smallest_y:
            return 1
        if biggest_x == smallest_x:
            return 1 / np.var(y) if (1 / np.var(y)) < 1 else 1
        if biggest_y == smallest_y:
            return 1 / np.var(x) if (1 / np.var(x)) < 1 else 1
    x = [(item - smallest_x) / (biggest_x - smallest_x) for item in x]
    y = [(item - smallest_y) / (biggest_y - smallest_y) for item in y]
    for i in range(length_ - s):
        ccs += (x[i + s]) * (y[i])
        pow_x += math.pow(x[i + s], 2)
        pow_y += math.pow(y[i], 2)
    else:
        dist_x = math.pow(pow_x, 0.5)
        dist_y = math.pow(pow_y, 0.5)
        dist_xy = dist_x * dist_y
        if dist_x == 0 or dist_y == 0:
            if dist_x == 0 and dist_y != 0:
                return 1 / np.var(y) if (1 / np.var(y)) < 1 else 1
            if dist_y == 0 and dist_x != 0:
                return 1 / np.var(x) if (1 / np.var(x)) < 1 else 1
            else:
                return 1
        cs = ccs / dist_xy
    return cs


def correlation_caculate(x, y, s=None):
    assert len(x) == len(y)
    if s == None:
        length_ = len(x)
        cs_list = []
        for i in range(int(length_ * 0.5)):
            cs_list.append(cacualte_cs_queue(x, y, i))
        KRD = max(cs_list)
    else:
        KRD = cacualte_cs_queue(x, y, s)
    return KRD


def get_time_series(files, group_instance_number, window_size, n_feature):
    '''
    :param files:   training files
    :param group_instance_number:   the number of databases in the unit
    :param window_size:
    :param n_feature:       KPI number
    :return:
    '''
    # Extract time series information in a dictionary，group number-database number-time point number
    time_series = {}
    time_series_classification = {}
    for file in files:
        # 文件格式:具体组_时间点_具体实例_数据类型
        format_name = file.split('\\')[-1].split('.')[0].split('_')
        group, point_index, instance, classification = format_name
        if group not in list(time_series.keys()):
            time_series[group] = {}
            time_series_classification[group] = {}
            for instance in range(group_instance_number):
                if instance not in list(time_series[group].keys()):
                    time_series[group][str(instance + 1)] = {}
                    time_series_classification[group][str(instance + 1)] = {}
        with open(file, 'r', encoding='utf-8') as f:
            group_window_time_series = pd.read_csv(f, sep=',')
            group_window_time_series = np.array(group_window_time_series)
            group_window_time_series = group_window_time_series.reshape(group_instance_number, window_size, n_feature)
            for group_index in range(group_instance_number):
                time_series[group][str(group_index + 1)][point_index] = group_window_time_series[group_index].tolist()
                time_series_classification[group][str(group_index + 1)][point_index] = classification
    return time_series, time_series_classification


def caculate_correlation_score(group_instance_number, group_quota_series, quota_index):
    '''
    :param group_instance_number:    the number of databases in the unit
    :param group_quota_series:      KPI information of all instances within a certain time window of a group
    :return:    correlation score table
    '''
    correlations = np.ones(shape=(group_instance_number, group_instance_number))
    # 计算group内部某一时间点某个属性的相关性分数
    for i in range(len(group_quota_series)):
        for j in range(len(group_quota_series)):
            if i == 0 or j == 0:
                if quota_index in config.master_slave_properties:
                    series_a = group_quota_series[i]
                    series_b = group_quota_series[j]
                    correlation = correlation_caculate(series_a, series_b, 0)
                    correlations[i, j] = correlations[j, i] = correlation
            else:
                if quota_index in config.slave_slave_properties:
                    series_a = group_quota_series[i]
                    series_b = group_quota_series[j]
                    correlation = correlation_caculate(series_a, series_b, 0)
                    correlations[i, j] = correlations[j, i] = correlation
    return correlations


def detection_anomalies(group_quota_series, correlations, quota_index, correlation_thresholds, tolerate_threshold,
                        anomalies_info):
    '''
    :param group_quota_series:      KPI information of all instances within a certain time window of a group
    :param correlations:        correlation score table for a certain KPI
    :param detection_info:      Abnormal information within a certain time window in the group
    :return:    Abnormal information within the time window
    '''
    level_1 = 0  # extreme deviation
    level_2 = 0  # slight deviation
    level_3 = 0  # correlation
    for i in range(len(group_quota_series)):
        for j in range(len(group_quota_series) - i):
            if i == 0 or j == 0:
                if quota_index in config.master_slave_properties:
                    if correlations[i][j] < correlation_thresholds[
                        config.master_slave_properties.index(quota_index)] and \
                            correlations[i][j] >= correlation_thresholds[
                        config.master_slave_properties.index(quota_index)] - tolerate_threshold:
                        level_2 += 1
                        anomalies_info['2'].append((quota_index, i + 1, j + 1, correlations[i][j]))
                    elif correlations[i][j] < correlation_thresholds[
                        config.master_slave_properties.index(quota_index)] - tolerate_threshold:
                        level_1 += 1
                        anomalies_info['1'].append((quota_index, i + 1, j + 1, correlations[i][j]))
                    else:
                        level_3 += 1
                else:
                    level_3 += 1
            else:
                if quota_index in config.slave_slave_properties:
                    if correlations[i][j] < correlation_thresholds[config.slave_slave_properties.index(quota_index)] and \
                            correlations[i][j] >= correlation_thresholds[
                        config.slave_slave_properties.index(quota_index)] - tolerate_threshold:
                        level_2 += 1
                        anomalies_info['2'].append((quota_index, i + 1, j + 1, correlations[i][j]))
                    elif correlations[i][j] < correlation_thresholds[
                        config.slave_slave_properties.index(quota_index)] - tolerate_threshold:
                        level_1 += 1
                        anomalies_info['1'].append((quota_index, i + 1, j + 1, correlations[i][j]))
                    else:
                        level_3 += 1
                else:
                    level_3 += 1
    anomalies_info['level_1'] += level_1
    anomalies_info['level_2'] += level_2
    anomalies_info['level_3'] += level_3
    return anomalies_info


class RMMTest:
    def __init__(self, correlation_thresholds, tolerate_threshold, tolerate_KPI, path):
        self.train_dir = path
        self.files = util.get_files(self.train_dir)
        self.window_size = 3 * 6
        self.group_instance_number = 5
        self.n_feature = 14
        self.tolerate_KPI = tolerate_KPI
        self.TP = 0
        self.TN = 0
        self.FP = 0
        self.FN = 0
        self.correlation_thresholds = correlation_thresholds
        self.tolerate_threshold = tolerate_threshold
        self.maximum_window_multiple = 3

    def caculate_abnormal_number(self, abnormal_str):
        # 判断是否检测到异常
        if abnormal_str == 'TP':
            self.TP += 1  # 成功检测到异常
        elif abnormal_str == 'FN':
            self.FN += 1  # 存在异常，但没检测到
        elif abnormal_str == 'FP':
            self.FP += 1  # 错误检测到异常
        else:
            self.TN += 1  # 不存在异常

    def caculate_rate(self, ):
        self.Precision = self.TP / (self.TP + self.FP)
        self.Recall = self.TP / (self.TP + self.FN)
        self.F1 = (2 * self.Precision * self.Recall) / (self.Precision + self.Recall)

    def epoch(self, ):
        time_series, time_series_classification = get_time_series(self.files, self.group_instance_number,
                                                                  self.window_size, self.n_feature)

        for group_index in list(time_series.keys()):
            flexible_window_size = self.window_size
            point_index = 0
            total_point_len = len(time_series[group_index]['1'].keys())
            while point_index < total_point_len:
                time_gap = 1
                # 1,2,3 represent their respective (KPI, i, j, correlation_score) pairs
                anomalies_info = {'1': [], '2': [], '3': [], 'level_1': 0, 'level_2': 0, 'level_3': 0}
                while flexible_window_size <= self.window_size * self.maximum_window_multiple and point_index < total_point_len:
                    for quota_index in range(self.n_feature):
                        group_quota_series = []
                        for instance_index in range(self.group_instance_number):
                            window_add = 0
                            current_time = point_index
                            window_series_feature = []
                            # Add longer time window series
                            while window_add < flexible_window_size and current_time < total_point_len:
                                window_series_feature.extend(
                                    time_series[group_index][str(instance_index + 1)][str(current_time)])
                                window_add += self.window_size
                                current_time += 1
                            quota_index_series = np.array(window_series_feature)[:, quota_index].tolist()
                            group_quota_series.append(quota_index_series)
                        correlations = caculate_correlation_score(self.group_instance_number, group_quota_series,
                                                                  quota_index)
                        # Determine whether the correlation score of the KPI meets the threshold requirements
                        anomalies_info = detection_anomalies(group_quota_series, correlations, quota_index,
                                                             self.correlation_thresholds, self.tolerate_threshold,
                                                             anomalies_info)

                    if anomalies_info['level_1'] > 0 or anomalies_info['level_2'] > self.tolerate_KPI:
                        time_start = 0
                        #
                        #  if an issue is detected in one window, an alarm will be issued.
                        while time_start < time_gap and (point_index + time_start) < total_point_len:
                            if time_series_classification[group_index]['1'][str(point_index + time_start)] != '0':
                                self.caculate_abnormal_number('TP')
                                break
                            time_start += 1
                        else:
                            self.caculate_abnormal_number('FP')
                        point_index += 1
                        break
                    elif anomalies_info['level_2'] < self.tolerate_KPI and anomalies_info['level_2'] > 0:
                        # observable, to be observed, need to extend longer time window data
                        flexible_window_size += self.window_size
                    else:
                        time_start = 0
                        while time_start < time_gap and (point_index + time_start) < total_point_len:
                            #  if an issue is detected in one window, an alarm will be issued.
                            if time_series_classification[group_index]['1'][str(point_index + time_start)] != '0':
                                self.caculate_abnormal_number('FN')
                                break
                            time_start += 1
                        else:
                            self.caculate_abnormal_number('TN')
                        point_index += 1
                        break
                    time_gap += 1
                else:
                    if point_index < total_point_len:
                        time_start = 0
                        while time_start < time_gap and (point_index + time_start) < total_point_len:
                            if time_series_classification[group_index]['1'][str(point_index + time_start)] != '0':
                                self.caculate_abnormal_number('TP')
                                break
                            time_start += 1
                        else:
                            self.caculate_abnormal_number('FP')
                        point_index += 1
        self.caculate_rate()


if __name__ == '__main__':
    '''
    # Recommended Thresholds
    # Sysbench_irregular 
    Sysbench_irregular_thresholds =  [0.92390353, 0.78476564, 0.84853898, 0.74522678, 0.18760985, 0.64012267,
    0.79291956, 0.96132011, 0.46611001, 0.13326597, 0.1119301,  0.85914802,
    0.04146568, 0.32331908] 
    Sysbench_irregular_tolerance_threshold = 0.3
    Sysbench_irregular_tolerance_KPI_upper = 0
    '''
    '''
    # Recommended Thresholds
    # Sysbench_periodic 
    Sysbench_periodic_thresholds =  [0.85890394, 0.23023118, 0.93844102, 0.74048112, 0.63481159, 0.31965017,
    0.91883372, 0.151212,   0.25254602, 0.84355629, 0.297864,   0.14174032,
    0.19026952, 0.44451241]
    Sysbench_periodic_tolerance_threshold = 0.3
    Sysbench_periodic_tolerance_KPI_upper = 2
    '''
    '''
    # Recommended Thresholds
    # Tencent_irregular
    Sysbench_periodic_thresholds =  [0.4054512,   0.14059641, 0.8012156, 0.2412513, 0.4018541, 0.41412841,
    0.9158411, 0.31265164, 0.402259841, 0.705481115, 0.10354841,  0.3048141,
    0.6284251, 0.5622513]
    Tencent_irregular_tolerance_threshold = 0.05
    Tencent_irregular_tolerance_KPI_upper = 2
    '''
    '''
    # Recommended Thresholds
    # Tencent_periodic
    Tencent_periodic_thresholds =  [0.301125,   0.240150, 0.80815498, 0.01441488, 0.40495841, 0.414791254,
    0.914845, 0.0318510, 0.4029841, 0.7058451, 0.2035812,  0.1098412,
    0.5205981, 0.262025654]
    Tencent_periodic_tolerance_threshold = 0.05
    Tencent_periodic_tolerance_KPI_upper = 2
    '''
    '''
    # Recommended Thresholds
    # TPCC_irregular
    TPCC_irregular_thresholds =  [0.271684   0.09240539 0.79812424 0.01442456 0.40495786 0.41479519
    0.89147074 0.05182895 0.47269694 0.68562806 0.2938266  0.10919667
    0.26208817 0.04205518]
    TPCC_irregular_tolerance_threshold = 0.1
    TPCC_irregular_tolerance_KPI_upper = 0
    '''
    # Recommended Thresholds
    # TPCC_periodic
    TPCC_periodic_thresholds = [0.311230, 0.1240520, 0.80812256, 0.01442425, 0.40495786, 0.41479519,
                                0.8914845, 0.0318510, 0.51269694, 0.70562806, 0.3038266, 0.10919667,
                                0.26202561, 0.03205551]
    TPCC_periodic_tolerance_threshold = 0.01
    TPCC_periodic_tolerance_KPI_upper = 2
    path = '../tpcc_periodic_test'
    rmm_case = RMMTest(TPCC_periodic_thresholds, TPCC_periodic_tolerance_threshold, TPCC_periodic_tolerance_KPI_upper,
                       path)
    rmm_case.epoch()
    print('F1:{}'.format(rmm_case.F1))
    print('TP:{}'.format(rmm_case.TP))
    print('TN:{}'.format(rmm_case.TN))
    print('FP:{}'.format(rmm_case.FP))
    print('FN:{}'.format(rmm_case.FN))
