import json
import yaml
import random
import pandas
import calendar
from datetime import date, datetime, timedelta

from person import Person
from json_encoders import PersonEncoder


def load_config():
    with open('example_config.yaml', 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as err:
            raise Exception(err)


def initialize_planning(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return {date(year, month, day): [] for day in range(1, num_days + 1)}


def initialize_team(config, num_days):
    employees = []
    for employee in config['employees']:
        p = Person(employee['first_name'], employee['last_name'], employee['gender'])

        if 'leaves' in employee:
            for leave in employee['leaves']:
                p.set_leave(start=leave['start_date'], end=leave['end_date'])

        if 'mandatory_shifts' in employee:
            for mandatory_day in employee['mandatory_shifts']:
                for leave_period in p.leaves:
                    if leave_period[0] <= mandatory_day <= leave_period[1]:
                        raise Exception(f'Mandatory shift {mandatory_day} is in a leave period')
                p.set_mandatory_shift(day=mandatory_day)
                p.set_leave(start=  mandatory_day - timedelta(days=3),
                            end=    mandatory_day - timedelta(days=1))

        if 'free_days' in employee:
            if isinstance(employee['free_days'], int):
                for _ in range(employee['free_days']):
                    free_day = date(config['year'], config['month'], random.randint(1, num_days))
                    if free_day not in p.mandatory_shift_days and free_day not in p.free_days:
                        try:
                            if all(leave['start_date'] <= free_day <= leave['end_date']
                                   for leave in employee.get('leaves', [])):
                                continue
                        except KeyError:
                            pass
                        p.free_days.append(free_day)
                        p.set_leave(start=free_day, end=free_day)
            elif isinstance(employee['free_days'], list):
                for free_day in employee['free_days']:
                    if free_day not in employee.get('mandatory_shifts', []):
                        p.free_days.append(free_day)
                        p.set_leave(start=free_day, end=free_day)
                    else:
                        raise Exception(f'Free day {free_day} is in a mandatory shift day')
        employees.append(p)
    return employees


def check_last_planning(employees, config):
    previous_planning = (date(config['year'], config['month'], 1) - timedelta(days=1)).strftime('planning_%Y_%#m.json')
    try:
        with open(previous_planning, 'r') as json_file:
            shifts = json.load(json_file)
            for shift in list(shifts.items())[-4:]:
                day = datetime.strptime(shift[0], '%Y-%m-%d').date()
                for e in employees:
                    for last_name in shift[1]:
                        if last_name == e.last_name:
                            e.in_shift(day)
    except FileNotFoundError:
        print('Last month\'s planning not found')


def backtrack(plan, day, team, max_people_per_shift, blacklist):

    # Exit case (plan is complete)
    if list(plan.values())[-1]:
        return plan

    # randomly mix the team (for equity)
    random.shuffle(team)

    # Check mandatory shifts first
    for person in team:
        if person.check_mandatory_shift(day):
            plan[day].append(person)
            person.in_shift(day)

    # Main loop
    for person in team:
        # check if available (not in leave)
        if not person.is_available(day):
            continue
        # check if in blacklist (backtracking)
        elif (person, day) in blacklist:
            continue
        # check if more than 2 people in shift
        elif len(plan[day]) >= max_people_per_shift:
            max_people_per_shift = 2
            break
        # check if genders match
        elif plan[day] and person.gender != plan[day][0].gender:
            continue
        # if all the above are met assign person to shift
        else:
            plan[day].append(person)
            person.in_shift(day)
    # If for loop exits without break (no person was found available)
    else:
        if not plan[day]:
            day -= timedelta(days=1)
            try:
                if len(plan[day]) == 2:
                    plan[day][0].remove_last_leave()
                    plan[day][1].remove_last_leave()
                    blacklist.append((plan[day][random.randint(0, 1)], day))
                elif len(plan[day]) == 1:
                    plan[day][0].remove_last_leave()
                    blacklist.append((plan[day][0], day))
                plan[day] = []
                for (person, d) in blacklist:
                    if d > day:
                        blacklist.remove((person, d))
            except KeyError:
                print('No possible solution!')
                exit()
            backtrack(plan, day, team, 1, blacklist)  # previous day

    backtrack(plan, day + timedelta(days=1), team, max_people_per_shift, blacklist)  # next day


# HELPER FUNCTIONS
def convert_plan_based_on_person(person_list: list, plan: dict):
    persons_dict = {person.last_name: [] for person in person_list}
    for person in person_list:
        for day, persons in plan.items():
            if person in persons:
                persons_dict[person.last_name].append('24')
            elif day in person.free_days:
                print(day)
                persons_dict[person.last_name].append('R')
            else:
                persons_dict[person.last_name].append('')
    return persons_dict


# GENERATE OUTPUT FUNCTIONS
def generate_json_planning(plan):
    planning_dict = dict((day.isoformat(), value) for (day, value) in plan.items())

    with open(f'planning_{config["year"]}_{config["month"]}.json', 'w') as outfile:
        json.dump(planning_dict, outfile, indent=4, cls=PersonEncoder)


def generate_excel_planning(person_list: list, plan: dict):
    persons_dict = convert_plan_based_on_person(person_list, plan)
    columns = [d.strftime('%d') for d in plan.keys()]
    df = pandas.DataFrame.from_dict(data=persons_dict, orient='index', columns=columns)
    df.to_excel(f'planning_{config["year"]}_{config["month"]}.xlsx')


def generate_mattermost_table(person_list: list, plan: dict):
    persons_dict = convert_plan_based_on_person(person_list, plan)
    plan_date = list(plan.keys())[0]
    month = {1: 'Ianuarie', 2: 'Februarie', 3: 'Martie', 4: 'Aprilie',
             5: 'Mai', 6: 'Iunie', 7: 'Iulie', 8: 'August',
             9: 'Septembrie', 10: 'Octombrie', 11: 'Noiembrie', 12: 'Decembrie'}
    print('Copiaza tot ce este mai jos si pune pe Mattermost in canalul Planificari:')
    print(f'#### Planificarea serviciilor la CRISC pentru luna {month[plan_date.month]} {plan_date.year}')
    print('||' + '|'.join([d.strftime('%d') for d in plan.keys()]) + '|')
    print('|:-|' + '|'.join(['-' for key in plan.keys()]) + '|')
    for person in persons_dict.keys():
        print(f'| {person} | ' + '|'.join(persons_dict[person]) + '|')


if __name__ == '__main__':
    config = load_config()
    planning = initialize_planning(config['year'], config['month'])
    num_days = calendar.monthrange(config['year'], config['month'])[1]
    employees = initialize_team(config, num_days)
    check_last_planning(employees, config)

    # Call to main function
    backtrack(plan=planning,
              day=list(planning.keys())[0],
              team=employees,
              max_people_per_shift=2,
              blacklist=[])

    # generate_json_planning(planning)
    # generate_excel_planning(employees, planning)
    generate_mattermost_table(employees, planning)