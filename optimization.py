from collections import namedtuple
import csv
from datetime import datetime
import math
import random

FlightCost = namedtuple('FlightCost', ['departure', 'arrival', 'price'])
Person = namedtuple('Person', ['name', 'home'])
Domain = namedtuple('Domain', ['min', 'max'])

def get_flights(schedule_file):
    flights = {}
    with open(schedule_file, 'r') as f:
        rows = csv.reader(f)
        for (origin, destination, departure, arrival, price)  in rows:
            flights.setdefault((origin, destination), [])
            flights[(origin, destination)].append(FlightCost(departure,
                arrival, int(price)))
    return flights

def get_minutes(date_string):
    d = datetime.strptime(date_string, '%H:%M')
    return d.hour * 60 + d.minute

def print_schedule(schedule, people, destination, flights):
    for (person_num, person) in enumerate(people):
        outbound = flights[(person.home, destination)][schedule[2 *
            person_num]]
        inbound = flights[(destination, person.home)][schedule[2 *
            person_num + 1]]
        print('%10s %3s %5s %5s $%3d %5s %5s $%3d' % (person.name, person.home,
            outbound.departure,
            outbound.arrival,
            outbound.price,
            inbound.departure,
            inbound.arrival,
            inbound.price
            ))

def schedule_cost(schedule, people, destination, flights):
    total_waiting_time = 0
    total_price = 0
    outbounds = [flights[(person.home, destination)][schedule[2 *
            person_num]] for (person_num, person) in enumerate(people)]
    inbounds = [flights[(destination, person.home)][schedule[2 *
            person_num + 1]] for (person_num, person) in enumerate(people)]

    last_outbound_arrival = max([get_minutes(outbound.arrival)
        for outbound in outbounds])
    first_inbound_departure = min([get_minutes(inbound.departure)
        for inbound in inbounds])

    for outbound in outbounds:
        total_price += outbound.price
        total_waiting_time += \
                last_outbound_arrival - get_minutes(outbound.arrival)
    for inbound in inbounds:
        total_price += inbound.price
        total_waiting_time += \
                get_minutes(inbound.departure) - first_inbound_departure
    time_weight = 1.0
    price_weight = 1.0
    return time_weight * total_waiting_time + price_weight * total_price

def schedule_costing(people, destination, flights):
    def costing(schedule):
        return schedule_cost(schedule, people, destination, flights)
    return costing

def random_optimize(domains, costing, attempts=100):
    minimum_cost = 9999999999
    best_schedule = None
    for attempt in range(attempts):
        schedule = [random.randint(domain.min, domain.max)
                for domain in domains]
        cost = costing(schedule)
        if cost <= minimum_cost:
            minimum_cost = cost
            best_schedule = schedule
    return best_schedule, minimum_cost

def hill_climb_optimize(domains, costing, attempts=100):
    minimum_cost = 999999999
    schedule = [random.randint(domain.min, domain.max) for domain in domains]
    for attempt in range(attempts):
        neighbours = []
        for (domain_num, domain) in enumerate(domains):
            if domain.min < schedule[domain_num]:
                neighbour = schedule[:]
                neighbour[domain_num] -= 1
                neighbours.append(neighbour)
            if schedule[domain_num] < domain.max:
                neighbour = schedule[:]
                neighbour[domain_num] += 1
                neighbours.append(neighbour)
        for neighbour in neighbours:
            cost = costing(neighbour)
            if cost <= minimum_cost:
                minimum_cost = cost
                schedule = neighbour

    return schedule, minimum_cost

def random_hill_climb_optimize(domains, costing, attempts=100):
    minimum_cost = 999999999
    schedule = [random.randint(domain.min, domain.max) for domain in domains]
    for attempt in range(attempts):
        neighbours = []
        for (domain_num, domain) in enumerate(domains):
            neighbour = schedule[:]
            neighbour[domain_num] = random.randint(domain.min, domain.max)
            neighbours.append(neighbour)

        for neighbour in neighbours:
            cost = costing(neighbour)
            if cost <= minimum_cost:
                minimum_cost = cost
                schedule = neighbour

    return schedule, minimum_cost

def simulated_annealing_optimize(domains, costing, attempts=100, cooling=0.95,
        verbose=False, step_size=1):
    best_schedule = [random.randint(domain.min, domain.max)
            for domain in domains]
    minimum_cost = costing(best_schedule)
    schedule = best_schedule
    current_cost = minimum_cost
    temperature = 100000

    def acceptance_probability(source_cost, destination_cost, temperature):
        if destination_cost < source_cost:
            return 1.0
        return math.exp(-(destination_cost - source_cost) / temperature)

    for attempt in range(attempts):
        # generate random neighbour
        neighbour = schedule[:]
        domain_num = random.randrange(len(domains))
        domain = domains[domain_num]
        direction = random.randint(-step_size, step_size)
        neighbour[domain_num] += direction
        if neighbour[domain_num] < domain.min:
            neighbour[domain_num] = domain.min
        elif domain.max < neighbour[domain_num]:
            neighbour[domain_num] = domain.max

        neighbour_cost = costing(neighbour)
        p = acceptance_probability(current_cost, neighbour_cost, temperature)

        if random.random() <= p:
            schedule = neighbour
            current_cost =  neighbour_cost
            if current_cost <= minimum_cost:
                minimum_cost = current_cost
                best_schedule = schedule

        temperature *= cooling
        if verbose:
            print('cost: %d\ttemp: %f\tp: %f' % (current_cost, temperature,
                p))

    return best_schedule, minimum_cost

def genetic_optimize(domains, costing, attempts=1000, population_size=50,
        elitism=0.2, mutation_probability=0.5):
    population = [[random.randint(domain.min, domain.max)
        for domain in domains] for i in range(population_size)]
    elite_size = int(population_size * elitism)

    def mutate(s):
        domain_num = random.randrange(0, len(domains))
        domain = domains[domain_num]
        result = s[:]
        result[domain_num] = random.randint(domain.min, domain.max)
        return result

    def crossover(s, t):
        start = random.randint(0, len(domains))
        end = random.randint(0, len(domains))
        if end < start:
            tmp = end
            end = start
            start = tmp

        result = s[:]
        for i in range(start, end):
            result[i] = t[i]
        return result

    for attempt in range(attempts):
        ranked_population = [(costing(p), p) for p in population]
        ranked_population.sort()
        elites = [p for (cost, p) in ranked_population[0:elite_size]]
        population = elites[:]

        # create mutations of the elites
        while len(population) < population_size:
            if random.random() < mutation_probability:
                s = elites[random.randrange(0, len(elites))]
                population.append(mutate(s))
            else:
                s = elites[random.randrange(0, len(elites))]
                t = elites[random.randrange(0, len(elites))]
                population.append(crossover(s, t))
        print('cost: %d' % (ranked_population[0][0],))

    return ranked_population[0][1], ranked_population[0][0]

def get_domains(people, destination, flights):
    domains = []
    for person in people:
        domains.append(Domain(0, len(flights[(person.home, destination)]) - 1))
        domains.append(Domain(0, len(flights[(destination, person.home)]) - 1))
    return domains

if __name__ == '__main__':
    schedule_file = 'schedule.txt'

    destination = 'LGA'
    flights = get_flights(schedule_file)
    people = [
            Person('Seymour', 'BOS'),
            Person('Franny', 'DAL'),
            Person('Zooey', 'CAK'),
            Person('Walt', 'MIA'),
            Person('Buddy', 'ORD'),
            Person('Les', 'OMA')
            ]

    domains = get_domains(people, destination, flights)
    costing = schedule_costing(people, destination, flights)
    #schedule, cost = random_optimize(domains, costing, 100)
    #schedule, cost = hill_climb_optimize(domains, costing, 100)
    #schedule, cost = random_hill_climb_optimize(domains, costing, 100)
    #schedule, cost = simulated_annealing_optimize(domains, costing, 1000,
            #cooling=0.98,verbose=False,step_size=3)
    schedule, cost = genetic_optimize(domains, costing, attempts = 100,
            population_size=400, elitism=0.1)

    print_schedule(schedule, people, destination, flights)
    print(schedule_cost(schedule, people, destination, flights))

