from detection import config
from detection.RMM import RMMTest
import random
import numpy as np
from multiprocessing import Pool


def indivdual_caculate_fitness(population, path):
    for ind in population[0]:
        ind.caculate_fitness(path)
    return population


class GA:
    class indivdual:
        def __init__(self, theta, tolerance_theta_list, max_KPI_deviation_tuple_upper):
            self.threshold = np.random.random((len(theta),))
            self.tolerance_theta_list = tolerance_theta_list
            self.tolerance_theta = tolerance_theta_list[random.randint(0, len(tolerance_theta_list) - 1)]
            self.tolerance_KPI = random.randint(0, max_KPI_deviation_tuple_upper)
            self.max_KPI_deviation_tuple_upper = max_KPI_deviation_tuple_upper
            self.fitness = 0

        def caculate_fitness(self, path):
            rmm_case = RMMTest(self.threshold, self.tolerance_theta, self.tolerance_KPI, path)
            rmm_case.epoch()
            self.fitness = rmm_case.F1

    def __init__(self, number, iterations, theta, tolerance_theta_upper, max_KPI_deviation_tuple_upper, path):
        self.number = number
        self.path = path
        self.iterations = iterations
        self.population = []
        self.theta = theta
        self.tolerance_theta_list = []
        self.max_KPI_deviation_tuple_upper = max_KPI_deviation_tuple_upper
        self.evict_number = int(number / 2)
        while tolerance_theta_upper > 0:
            self.tolerance_theta_list.append(tolerance_theta_upper)
            tolerance_theta_upper -= 0.1
        for i in range(number):
            ind = GA.indivdual(theta, self.tolerance_theta_list, max_KPI_deviation_tuple_upper)
            self.population.append(ind)

    def selection(self, indivduals_pro):
        ind1, ind2 = np.random.choice(len(indivduals_pro), 2, p=indivduals_pro)
        return self.population[ind1], self.population[ind2]

    def crossover(self, parent1, parent2):
        child1, child2 = GA.indivdual(parent1.threshold, self.tolerance_theta_list,
                                      self.max_KPI_deviation_tuple_upper), GA.indivdual(parent2.threshold,
                                                                                        self.tolerance_theta_list,
                                                                                        self.max_KPI_deviation_tuple_upper)
        a = random.randint(0, len(parent1.threshold) - 1)
        indexs = np.random.choice(np.arange(len(parent1.threshold)), size=a, replace=False)
        for index in indexs:
            swap = child1.threshold[index]
            child1.threshold[index] = child2.threshold[index]
            child2.threshold[index] = swap
        ind1_tolerance = np.random.choice([0, 1], 1, p=[0.5, 0.5])
        ind2_tolerance = np.random.choice([0, 1], 1, p=[0.5, 0.5])
        child1.tolerance_theta = parent1.tolerance_theta if ind1_tolerance == 0 else parent2.tolerance_theta
        child2.tolerance_theta = parent2.tolerance_theta if ind2_tolerance == 0 else parent1.tolerance_theta
        child1.tolerance_KPI = parent1.tolerance_KPI if ind1_tolerance == 0 else parent2.tolerance_KPI
        child2.tolerance_KPI = parent2.tolerance_KPI if ind2_tolerance == 0 else parent1.tolerance_KPI
        return child1, child2

    def mutation(self, indivduals_pro):
        delta = 0.1
        ind = self.population[np.random.choice(len(indivduals_pro), 1, p=indivduals_pro)[0]]
        mutation_ind = GA.indivdual(ind.threshold, self.tolerance_theta_list,
                                    self.max_KPI_deviation_tuple_upper)
        for threshold_index in range(len(mutation_ind.threshold)):
            mutation_type = np.random.choice([0, 1], 1, p=[0.5, 0.5])
            mutation_ind.threshold[threshold_index] = mutation_ind.threshold[
                                                          threshold_index] - delta if mutation_type == 0 else \
                mutation_ind.threshold[threshold_index] + delta
        mutation_ind.tolerance_KPI = random.randint(0, self.max_KPI_deviation_tuple_upper)
        mutation_ind.tolerance_theta = mutation_ind.tolerance_theta_list[
            random.randint(0, len(mutation_ind.tolerance_theta_list) - 1)]
        return mutation_ind

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

    def pool_caculate_fitness(self, population_tmp, pool_number):
        receive_son_population = []
        for i in range(pool_number):
            son_population = self.pool.apply_async(indivdual_caculate_fitness, (population_tmp[i], self.path,))
            receive_son_population.append(son_population)
        self.pool.close()
        self.pool.join()
        population = []
        for ind in receive_son_population:
            population.extend(ind.get()[0])
        return population

    def implement(self, pool_number):
        max_F1 = 0
        population_tmp = self.split_population(self.population, pool_number)
        self.population = self.pool_caculate_fitness(population_tmp, pool_number)
        for i in range(self.iterations):
            self.population.sort(key=lambda ind: ind.fitness, reverse=True)
            if len(self.population) >= 1:
                max_epoch_ind = self.population[0]
                if max_epoch_ind.fitness > max_F1:
                    max_F1 = self.population[0].fitness
                    with open("..//log//info.txt", 'a') as f:
                        info = 'F1-Score:{}  correlation_theta:{}  tolerance_theta:{}  max_KPI_deviation_tuple_upper:{}\n'.format(
                            max_F1,
                            max_epoch_ind.threshold,
                            max_epoch_ind.tolerance_theta,
                            max_epoch_ind.tolerance_KPI)
                        print(info)
                        f.write(info)
            else:
                print('没有元素')
                exit(0)
            while len(self.population) > self.number - self.evict_number:
                self.population.pop()
            indivduals_fitness = [ind.fitness for ind in self.population]
            total_indivduals_fitness = sum(indivduals_fitness)
            indivduals_pro = [fitness / total_indivduals_fitness for fitness in indivduals_fitness]
            crossover = 0
            crossover_list = []
            while crossover < int(self.evict_number / 2):
                ind1, ind2 = self.selection(indivduals_pro)
                ind1, ind2 = self.crossover(ind1, ind2)
                crossover_list.append(ind1)
                crossover_list.append(ind2)
                crossover += 2
            crossover_list_tmp = self.split_population(crossover_list, pool_number)
            crossover_list = self.pool_caculate_fitness(crossover_list_tmp, pool_number)
            mutation = 0
            mutation_list = []
            while mutation < int(self.number - len(self.population) - len(crossover_list)):
                ind = self.mutation(indivduals_pro)
                mutation_list.append(ind)
                mutation += 1
            mutation_list_tmp = self.split_population(mutation_list, pool_number)
            mutation_list = self.pool_caculate_fitness(mutation_list_tmp, pool_number)
            self.population.extend(crossover_list)
            self.population.extend(mutation_list)


if __name__ == '__main__':
    number = 50
    iterations = 30
    tolerance_theta_upper = 0.4
    max_KPI_deviation_tuple_upper = 8
    pool_number = 10
    path = '../tencent_periodic_test'
    ga = GA(number, iterations, config.theta, tolerance_theta_upper, max_KPI_deviation_tuple_upper, path)
    ga.implement(pool_number)
