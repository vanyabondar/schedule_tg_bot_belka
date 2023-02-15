import random

from integration_from_db_to_ga import ShiftGA, WorkerGA
from typing import Optional


class GeneticAlgorithm:
    shifts: list[ShiftGA]
    workers: list[WorkerGA]
    population: Optional[list[list[WorkerGA]]]

    def __init__(self, shifts: list[ShiftGA], workers: list[WorkerGA]):
        self.shifts = shifts
        self.workers = workers
        self.population = None

    def get_individual(self) -> list[WorkerGA]:
        ind = []
        for shift in self.shifts:
            ind.append(random.choice(shift.available_workers))
        return ind

    def get_population(self, number_of_individuals: int) -> list[list[WorkerGA]]:
        population = [self.get_individual() for _ in range(number_of_individuals)]
        return population

    def fitness_calculation(self, individual: list[WorkerGA]) -> (float, int, int):
        rating = {worker.id: worker.rating for worker in self.workers}
        empty_gen = 0
        for i in range(len(individual)):
            if not individual[i].is_empty():
                rating[individual[i].id] += (
                        self.shifts[i].cost
                        * individual[i].coefficient)
            else:
                empty_gen += 1
        max_count = [max(individual.count(x) for x in individual)]

        avr = sum(rating.values()) / len(rating)
        mark = sum(abs(rating[worker] - avr) ** 2 for worker in rating)
        return empty_gen, max_count, mark

    def individual_mutation(self, individual: list[WorkerGA]) -> list[WorkerGA]:
        new_individual = individual.copy()

        # only one gen will get a mutation
        gen_index = random.randint(0, len(individual) - 1)
        new_individual[gen_index] = random.choice(
            self.shifts[gen_index].available_workers)

        return new_individual

    def selection(self, number_of_individuals: int) -> None:
        population_with_marks = [
            {'individual': ind, 'rating': self.fitness_calculation(ind)}
            for ind in self.population
        ]
        population_with_marks.sort(key=lambda ind: ind['rating'])

        population_slice = population_with_marks[:number_of_individuals]
        self.population = [raw['individual'] for raw in population_slice]

    @staticmethod
    def get_child(ind1, ind2):
        child = []
        for i in range(len(ind1)):
            child.append(random.choice((ind1[i], ind2[i])))
        return child

    def pairing(self, number_of_pairing: int) -> None:
        children = []
        for i in range(number_of_pairing):
            children.append(
                GeneticAlgorithm.get_child(
                    random.choice(self.population),
                    random.choice(self.population))
            )
        self.population.extend(children)

    def mutate(self, mutation_probability: float) -> None:
        for i in range(1, len(self.population)):
            if random.random() < mutation_probability:
                self.population[i] = self.individual_mutation(
                    self.population[i])

    def next_generation(
            self,
            number_of_individuals: int,
            number_of_pairing: int,
            mutation_probability: float
    ) -> None:
        self.mutate(mutation_probability)
        self.pairing(number_of_pairing)
        self.selection(number_of_individuals)

    def calc_schedule(
            self, number_of_generation: int,
            number_of_individuals: int,
            number_of_pairing: int,
            mutation_probability: float
    ) -> (list[WorkerGA], float):

        self.population = self.get_population(number_of_individuals)

        for i in range(number_of_generation):
            self.next_generation(
                number_of_individuals, number_of_pairing, mutation_probability
            )
            # print(f'Gen #{i}: {self.population[0]}, fitness: \
            #     {self.fitness_calculation(self.population[0])}')

        self.update_shifts(self.population[0])
        return self.shifts, self.fitness_calculation(self.population[0])

    def update_shifts(self, final_population: list[WorkerGA]):
        for i, shift in enumerate(self.shifts):
            if not final_population[i].is_empty():
                shift.final_worker = final_population[i]
