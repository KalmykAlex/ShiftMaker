from datetime import date, timedelta


class Person:
    def __init__(self, first_name, last_name, gender):
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.leaves = []
        self.mandatory_shift_days = []

    def __repr__(self):
        return f'{self.first_name} {self.last_name}'

    def set_leave(self, start: date, end: date):
        if start > end:
            raise Exception('DateError: leave starts after it ends')
        else:
            self.leaves.append((start, end))

    def remove_last_leave(self):
        self.leaves.pop()

    def is_available(self, day: date):
        for leave in self.leaves:
            if leave[0] <= day <= leave[1]:
                return False
        return True

    def set_mandatory_shift(self, day: date):
        self.mandatory_shift_days.append(day)

    def del_mandatory_shift(self, day: date):
        self.mandatory_shift_days.remove(day)

    def check_mandatory_shift(self, day):
        for d in self.mandatory_shift_days:
            if d == day:
                return True
        return False

    def in_shift(self, day: date):
        self.set_leave(day, day + timedelta(days=3))
