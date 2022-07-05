from detection import config
from detection.RMM import RMMTest
import random
import numpy as np
from multiprocessing import Pool
import math


def indivdual_caculate_score(population, path):
    for ind in population[0]:
        ind.caculate_score(path)
    return population


def indivdual_climb_process(population, path, learn_rate):
    for ind in population[0]:
        old_threshold = ind.threshold
        old_score = ind.score
        old_tolerate_KPI = ind.tolerance_KPI
        old_tolerance_theta = ind.tolerance_theta
        ind.generate_new_threshold(learn_rate)
        ind.caculate_score(path)

        if ind.score <= old_score:
            pro = math.pow(math.exp(1), -(old_score - ind.score))
            p = np.array([pro, 1 - pro])
            index = np.random.choice([0, 1], p=p.ravel())
            if index == 1:
                ind.threshold = old_threshold
                ind.score = old_score
                ind.tolrerance_KPI = old_tolerate_KPI
                ind.tolrerance_theta = old_tolerance_theta
    return population


class HillClimbing:
    class indivdual:
        def __init__(self, theta, tolerance_theta_list, tolerance_KPI_upper):
            self.threshold = np.random.random((len(theta),))
            self.tolerance_theta_list = tolerance_theta_list
            self.tolerance_theta = tolerance_theta_list[random.randint(0, len(tolerance_theta_list) - 1)]
            self.tolerance_KPI = random.randint(0, tolerance_KPI_upper)
            self.tolerance_KPI_upper = tolerance_KPI_upper
            self.score = 0

        def caculate_score(self, path):
            rmm_case = RMMTest(self.threshold, self.tolerance_theta, self.tolerance_KPI, path)
            rmm_case.epoch()
            self.score = rmm_case.F1

        def generate_new_threshold(self, learn_rate):
            tolerate_KPI = random.randint(0, self.tolerance_KPI_upper)
            tolerance_theta = self.tolerance_theta_list[random.randint(0, len(self.tolerance_theta_list) - 1)]
            for i in range(len(self.threshold)):
                old_theta = self.threshold[i]
                operate = random.randint(0, 2)
                if operate == 0:
                    new_theta = old_theta + learn_rate + round(random.uniform(0, 0.1), 2)
                    new_theta = old_theta if new_theta < 0 else new_theta
                    new_theta = 1 if new_theta > 1 else new_theta
                else:
                    new_theta = old_theta - learn_rate - round(random.uniform(0, 0.1), 2)
                    new_theta = old_theta if new_theta < 0 else new_theta
                    new_theta = 1 if new_theta > 1 else new_theta
                self.threshold[i] = new_theta
            self.tolerate_KPI = tolerate_KPI
            self.tolerance_theta = tolerance_theta

    def __init__(self, number, iterations, theta, tolerance_theta_upper, tolerance_KPI_upper, path):
        self.number = number
        self.path = path
        self.iterations = iterations
        self.population = []
        self.theta = theta
        self.tolerance_theta_list = []
        self.tolerance_KPI_upper = tolerance_KPI_upper
        while tolerance_theta_upper > 0:
            self.tolerance_theta_list.append(tolerance_theta_upper)
            tolerance_theta_upper -= 0.1
        for i in range(number):
            ind = HillClimbing.indivdual(theta, self.tolerance_theta_list, tolerance_KPI_upper)
            self.population.append(ind)

    def split_population(self, population, pool_number):
        self.pool = Pool(pool_number)
        gap = int(len(population) / pool_number)
        population_tmp = []
        for i in range(0, len(population), gap):
            if i + gap > len(population):
                population_tmp.append(population[i:len(population) - 1])
            else:
                population_tmp.append([population[i:i + gap]])
        return population_tmp

    def pool_caculate_score(self, population_tmp, pool_number):
        receive_son_population = []
        for i in range(pool_number):
            son_population = self.pool.apply_async(indivdual_caculate_score, (population_tmp[i], self.path,))
            receive_son_population.append(son_population)
        self.pool.close()
        self.pool.join()
        population = []
        for ind in receive_son_population:
            population.extend(ind.get()[0])
        return population

    def pool_climb_process(self, population_tmp, pool_number, learn_rate):
        receive_son_population = []
        for i in range(pool_number):
            son_population = self.pool.apply_async(indivdual_climb_process, (population_tmp[i], self.path, learn_rate,))
            receive_son_population.append(son_population)
        self.pool.close()
        self.pool.join()
        population = []
        for ind in receive_son_population:
            population.extend(ind.get()[0])
        return population

    def climb(self, pool_number, learn_rate):
        population_tmp = self.split_population(self.population, pool_number)
        self.population = self.pool_caculate_score(population_tmp, pool_number)
        max_F1 = 0
        for i in range(self.iterations):
            population_tmp = self.split_population(self.population, pool_number)
            self.population = self.pool_climb_process(population_tmp, pool_number, learn_rate)
            self.population.sort(key=lambda ind: ind.score, reverse=True)
            if len(self.population) >= 1:
                max_epoch_ind = self.population[0]
                if max_epoch_ind.score > max_F1:
                    max_F1 = self.population[0].score
                    with open("..//log//info.txt", 'a') as f:
                        info = 'F1-Score:{}  correlation_theta:{}  tolerance_theta:{}  tolerate_KPI:{}\n'.format(
                            max_F1,
                            max_epoch_ind.threshold,
                            max_epoch_ind.tolerance_theta,
                            max_epoch_ind.tolerance_KPI)
                        print(info)
                        f.write(info)
            else:
                print('no elements')
                exit(0)


if __name__ == '__main__':
    learn_rate = 0.1
    number = 100
    iterations = 20
    tolerance_theta_upper = 0.4
    tolerance_KPI_upper = 8
    pool_number = 5
    path = '../tencent_irregular_test'
    ga = HillClimbing(number, iterations, config.theta, tolerance_theta_upper, tolerance_KPI_upper, path)
    ga.climb(pool_number, learn_rate)
