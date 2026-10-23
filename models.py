from abc import ABC, abstractmethod

# Technique: OOP Encapsulation & Inheritance (Member parent class)
class Member:
    def __init__(self, user_id, username, email):
        self._user_id = user_id
        self._username = username
        self._email = email

    @property
    def user_id(self):
        return self._user_id

    @property
    def username(self):
        return self._username

    @property
    def email(self):
        return self._email

    # Technique: Polymorphism (Base method)
    def get_role_permissions(self):
        return ["VIEW_GROUP", "ADD_EXPENSE"]


# Technique: Inheritance (Admin child class)
class Admin(Member):
    def __init__(self, user_id, username, email):
        super().__init__(user_id, username, email)

    # Technique: Polymorphism (Overridden method)
    def get_role_permissions(self):
        permissions = super().get_role_permissions()
        permissions.extend(["MANAGE_MEMBERS", "RENAME_GROUP", "DELETE_GROUP"])
        return permissions


# Technique: Abstract Base Class & Polymorphism
class Split(ABC):
    def __init__(self, total_amount, participants):
        self._total_amount = total_amount
        self._participants = participants

    @abstractmethod
    def calculate_shares(self, input_values=None):
        """Abstract method overridden by concrete split implementations."""
        pass


class EqualSplit(Split):
    def calculate_shares(self, input_values=None):
        """Splits the total equally, distributing remaining cents to the first member."""
        if not self._participants:
            return {}
        
        total_cents = int(round(self._total_amount * 100))
        num_people = len(self._participants)
        base_share_cents = total_cents // num_people
        remainder_cents = total_cents % num_people
        
        shares = {}
        for index, user_id in enumerate(self._participants):
            # Give remainder cents to the first participant
            person_cents = base_share_cents + (remainder_cents if index == 0 else 0)
            shares[user_id] = round(person_cents / 100.0, 2)
            
        return shares


class ByAmountSplit(Split):
    def calculate_shares(self, input_values):
        """Splits by exact amounts provided per participant."""
        shares = {}
        sum_cents = 0
        total_cents = int(round(self._total_amount * 100))
        
        for user_id in self._participants:
            amt = float(input_values.get(user_id, 0.0))
            amt_cents = int(round(amt * 100))
            shares[user_id] = round(amt_cents / 100.0, 2)
            sum_cents += amt_cents
            
        if sum_cents != total_cents:
            raise ValueError(f"Sum of split amounts (${sum_cents/100:.2f}) must equal total (${self._total_amount:.2f}).")
            
        return shares


class ByPercentageSplit(Split):
    def calculate_shares(self, input_values):
        """Splits by percentages provided per participant."""
        shares = {}
        total_pct = 0.0
        
        for user_id in self._participants:
            pct = float(input_values.get(user_id, 0.0))
            total_pct += pct
            amt = round((self._total_amount * pct) / 100.0, 2)
            shares[user_id] = amt
            
        if abs(total_pct - 100.0) > 0.01:
            raise ValueError(f"Total percentage ({total_pct:.1f}%) must equal 100%.")
            
        return shares