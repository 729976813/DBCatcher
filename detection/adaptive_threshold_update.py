from detection import config
from detection.RMM import RMMTest
import random


def rate_update_correlation(theta, learn_rate, iterations, path):
    F1_max = 0
    for theta_index in range(len(theta)):
        old_theta = theta[theta_index]
        tolerate_KPI = random.randint(0, 6)
        tolerance_theta = round(random.uniform(0, 0.3), 1)
        for i in range(iterations):
            operate = random.randint(0, 2)
            if operate == 0:
                new_theta = old_theta + learn_rate + round(random.uniform(0, 0.1), 2)
                new_theta = old_theta if new_theta < 0 else new_theta
                new_theta = 1 if new_theta > 1 else new_theta
            else:
                new_theta = old_theta - learn_rate - round(random.uniform(0, 0.1), 2)
                new_theta = old_theta if new_theta < 0 else new_theta
                new_theta = 1 if new_theta > 1 else new_theta
            theta[theta_index] = new_theta
            rmm_case = RMMTest(theta, tolerance_theta, tolerate_KPI, path)
            rmm_case.epoch()
            if rmm_case.F1 > F1_max:
                with open("..//log//info.txt", 'a') as f:
                    info = 'F1-Score:{}  correlation_theta:{}  tolerance_theta:{}  tolerate_KPI:{}\n'.format(
                        rmm_case.F1,
                        theta,
                        tolerance_theta,
                        tolerate_KPI)
                    print(info)
                    f.write(info)
                F1_max = rmm_case.F1
            else:
                theta[theta_index] = old_theta
            old_theta = new_theta
        print('{} threshold learning completed'.format(kpi_name[theta_index]))


if __name__ == '__main__':
    learn_rate = 0.1
    iterations = 20
    kpi_name = ["BytesReceived", "BytesSent", "RealCapacity", "Tps", "Qps", "Queries", "ComUpdate", "ComInsert",
                "InnodbBufferPoolReadRequests", "InnodbRowsRead", "InnodbDataWrites", "CpuUseRate", "InnodbRowsDeleted",
                "InnodbRowsInserted", "InnodbRowsUpdated", "InnodbRowsRead", "InnodbDataWritten", "InnodbDataWrites"]
    path = '../sysbench_periodic_test'
    rate_update_correlation(config.theta, learn_rate, iterations, path)
