
class Drug:
    def __init__(self, name, code, conc, colour, dose, units):
        self.name = name
        self.code = code
        self.conc = conc
        self.colour = colour
        self.dose = dose
        self.units = units

    def __format__(self, fmt):
        label = "[" + self.colour + "]" + '\u2587' * 10 + "[/" + self.colour + "]"
        return f"{label} - {self.name}"

drug_db = {
        "5208063000318": Drug("Ondansetron","5208063000318","2 mg/mL",
                              "#faaa94", 4, "mg"),
        "5012727906751": Drug("Remifentanil", "5012727906751", None,
                              "#71c5e8", None, "mcg"),
        "4260274650448": Drug("Clonidine", "4260274650448", "150 mcg/mL",
                              "#d6bfdd", 30, "mcg"),
        "5016386033322": Drug("Dexamethasone", "5016386033322", "3.3 mg/mL",
                              "#ffffff", 6.6, "mg"),
        "5060130131390": Drug("Rocuronium", "5060130131390", "10 mg/mL",
                              "#f9423a", 30, "mg"),
        "5014124170681": Drug("Fentanyl", "5014124170681", "50 mcg/mL",
                              "#71c5e8", 50, "mcg"),
        "5014124170872": Drug("Suxamethonium", "5014124170872", "50 mg/mL",
                              "#f9423a", 50, "mg"),
}


drugs = [
    {
        "name": "Ondansetron",
        "code": "5208063000318",
        "conc": "2 mg/mL",
        "colour": "#faaa94",
        "dose": 4,
        "units": "mg",
    },
    {
        "name": "Remifentanil",
        "code": "5012727906751",
        "conc": "2 mg",
        "colour": "#71c5e8",
        "dose": 100,
        "units": "mcg",
    },
    {
        "name": "Clonidine",
        "code": "4260274650448",
        "conc": "150 mcg/mL",
        "colour": "#d6bfdd",
        "dose": 30,
        "units": "mcg",
    },
    {
        "name": "Dexamethasone",
        "code": "5016386033322",
        "conc": "3.3 mg/mL",
        "colour": "#ffffff",
        "dose": 6.6,
        "units": "mg",
    },
    {
        "name": "Rocuronium",
        "code": "5060130131390",
        "conc": "10 mg/mL",
        "colour": "#f9423a",
        "dose": 30,
        "units": "mg",
    },
    {
        "name": "Fentanyl",
        "code": "5014124170681",
        "conc": "50 mcg/mL",
        "colour": "#71c5e8",
        "dose": 50,
        "units": "mcg",
    },
    {
        "name": "Suxamethonium",
        "code": "5014124170872",
        "conc": "50 mg/mL",
        "colour": "#f9423a",
        "dose": 50,
        "units": "mg",
    },
]
