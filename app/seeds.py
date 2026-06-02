"""Seed danych testowych — uruchamiane przez `flask seed`.

Tworzy demonstracyjny zestaw użytkowników, hodowli i zwierząt z rodowodami,
żeby aplikacja od razu wyglądała sensownie. Idempotentne: powtórne wywołanie
NIE duplikuje danych (sprawdza po emailach).
"""

from __future__ import annotations

from datetime import date

import click
from flask import Flask

from .extensions import db
from .models.animal import Animal
from .models.farm import Farm
from .models.user import User


def register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed_command():
        """Wgraj przykładowy zestaw hodowli i zwierząt do bazy."""
        with app.app_context():
            count = run_seed()
            click.echo(f"Seed gotowy. Dodano {count} nowych rekordów.")


def _ensure_user(email: str, name: str, password: str = "demo12345") -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(email=email, display_name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def _ensure_farm(owner: User, **kwargs) -> Farm:
    farm = Farm.query.filter_by(owner_id=owner.id, name=kwargs["name"]).first()
    if farm:
        return farm
    farm = Farm(owner_id=owner.id, **kwargs)
    db.session.add(farm)
    db.session.commit()
    return farm


def _ensure_animal(farm: Farm, **kwargs) -> Animal:
    animal = Animal.query.filter_by(farm_id=farm.id, name=kwargs["name"]).first()
    if animal:
        return animal
    animal = Animal(farm_id=farm.id, **kwargs)
    db.session.add(animal)
    db.session.commit()
    return animal


def run_seed() -> int:
    """Tworzy testowe konta, hodowle i zwierzęta. Zwraca przybliżoną liczbę dodanych rekordów."""
    before = (
        db.session.query(User).count()
        + db.session.query(Farm).count()
        + db.session.query(Animal).count()
    )

    # Użytkownicy
    anna = _ensure_user("anna@hodowla.test", "Anna Kowalska")
    marek = _ensure_user("marek@hodowla.test", "Marek Wiśniewski")
    katarzyna = _ensure_user("kasia@hodowla.test", "Katarzyna Lis")
    piotr = _ensure_user("piotr@hodowla.test", "Piotr Zając")
    julia = _ensure_user("julia@hodowla.test", "Julia Nowak")
    andrzej = _ensure_user("andrzej@hodowla.test", "Andrzej Dąbrowski")

    # Hodowle
    farm_wiatr = _ensure_farm(
        anna,
        name="Stadnina Wschodni Wiatr",
        species="horse",
        description=(
            "Hodowla koni arabskich czystej krwi. Od 1992 roku selekcjonujemy "
            "linie rodowodowe pod kątem temperamentu, eksterieru i dzielności. "
            "Pochodzimy z Janowa Podlaskiego."
        ),
        city="Janów Podlaski",
        voivodeship="lubelskie",
        latitude=52.1953,
        longitude=23.2008,
        is_verified=True,
        contact_email="kontakt@wschodniwiatr.test",
        contact_phone="+48 600 100 200",
        website="https://wschodniwiatr.test",
    )

    farm_border = _ensure_farm(
        marek,
        name="Border Collies z Pszczyny",
        species="dog",
        description=(
            "Hodowla psów rasowych Border Collie zarejestrowana w ZKwP. "
            "Stawiamy na zdrowie, charakter i predyspozycje do pracy."
        ),
        city="Pszczyna",
        voivodeship="śląskie",
        latitude=49.9786,
        longitude=18.9447,
        is_verified=True,
        contact_email="hodowla@bcpszczyna.test",
        contact_phone="+48 601 234 567",
        website="https://bcpszczyna.test",
    )

    farm_golden = _ensure_farm(
        katarzyna,
        name="Kennel Złoty Liść",
        species="dog",
        description=(
            "Golden Retriever — psy rodzinne i terapeutyczne. "
            "Wszystkie szczeniaki przechodzą badania genetyczne."
        ),
        city="Gdańsk",
        voivodeship="pomorskie",
        latitude=54.3520,
        longitude=18.6466,
        is_verified=True,
        contact_email="kennel@zloty-lisc.test",
        contact_phone="+48 504 100 200",
        website="",
    )

    farm_majka = _ensure_farm(
        piotr,
        name="Stadnina Mała Wieś",
        species="horse",
        description=(
            "Konie półkrwi polskiej. Specjalizujemy się w hodowli koni "
            "skokowych z dobrym pochodzeniem po liniach holsztyńskich."
        ),
        city="Mała Wieś",
        voivodeship="mazowieckie",
        latitude=52.4400,
        longitude=20.1300,
        is_verified=False,
        contact_email="biuro@stadnina-malawies.test",
        contact_phone="+48 602 333 444",
        website="",
    )

    farm_koty = _ensure_farm(
        julia,
        name="Kocia Łapka — Maine Coon",
        species="cat",
        description=(
            "Hodowla kotów rasy Maine Coon. Wszystkie nasze koty są testowane "
            "DNA pod kątem HCM i SMA. Rodowody FIFe."
        ),
        city="Poznań",
        voivodeship="wielkopolskie",
        latitude=52.4064,
        longitude=16.9252,
        is_verified=True,
        contact_email="kotylapka@kotylapka.test",
        contact_phone="+48 605 100 100",
        website="https://kotylapka.test",
    )

    farm_szefa = _ensure_farm(
        andrzej,
        name="Hodowla Stado Białego Domu",
        species="dog",
        description="Owczarki niemieckie linii pracujących. Hodowla od 1998 roku.",
        city="Warszawa",
        voivodeship="mazowieckie",
        latitude=52.2297,
        longitude=21.0122,
        is_verified=False,
        contact_email="bialydom@bialydom.test",
        contact_phone="+48 600 700 800",
        website="",
    )

    # Zwierzęta — najpierw rodzice (bez parent_id), potem dzieci.

    # KONIE ARABSKIE (Stadnina Wschodni Wiatr)
    arab_emir = _ensure_animal(
        farm_wiatr,
        name="Emir",
        species="horse",
        breed="Koń arabski",
        sex="male",
        birth_date=date(2014, 4, 12),
        color="Siwy",
        registration_number="PL-AR-2014-001",
        title="Czempion Polski 2018",
        description="Ogier hodowlany, doskonałe pochodzenie po linii Bask.",
        available_for_breeding=True,
    )
    arab_perla = _ensure_animal(
        farm_wiatr,
        name="Perła",
        species="horse",
        breed="Koń arabski",
        sex="female",
        birth_date=date(2015, 5, 22),
        color="Kasztanowata",
        registration_number="PL-AR-2015-014",
        description="Klacz reprodukcyjna, źrebięta po niej osiągają wysokie ceny.",
        available_for_breeding=True,
    )
    arab_aida = _ensure_animal(
        farm_wiatr,
        name="Aida",
        species="horse",
        breed="Koń arabski",
        sex="female",
        birth_date=date(2019, 6, 1),
        color="Siwa",
        registration_number="PL-AR-2019-022",
        description="Córka Emira i Perły. Wszechstronnie utalentowana.",
        sire_id=arab_emir.id,
        dam_id=arab_perla.id,
        available_for_breeding=False,
    )
    arab_sokol = _ensure_animal(
        farm_wiatr,
        name="Sokół",
        species="horse",
        breed="Koń arabski",
        sex="male",
        birth_date=date(2020, 3, 14),
        color="Gniady",
        registration_number="PL-AR-2020-031",
        sire_id=arab_emir.id,
        dam_id=arab_perla.id,
        description="Bratanek Aidy, niezwykle żywiołowy.",
        available_for_breeding=False,
    )

    # BORDER COLLIES (Pszczyna)
    bc_rex = _ensure_animal(
        farm_border,
        name="Rex",
        species="dog",
        breed="Border Collie",
        sex="male",
        birth_date=date(2017, 9, 3),
        color="Czarno-biały",
        registration_number="ZKwP-BC-17-451",
        title="Champion Polski",
        description="Pies pracujący, wybitny w agility i pasterstwie.",
        available_for_breeding=True,
    )
    bc_luna = _ensure_animal(
        farm_border,
        name="Luna",
        species="dog",
        breed="Border Collie",
        sex="female",
        birth_date=date(2018, 5, 11),
        color="Niebiesko-biały",
        registration_number="ZKwP-BC-18-522",
        description="Suka hodowlana, doskonała intuicja stadna.",
        available_for_breeding=True,
    )
    bc_misza = _ensure_animal(
        farm_border,
        name="Misza",
        species="dog",
        breed="Border Collie",
        sex="female",
        birth_date=date(2021, 2, 18),
        color="Czarno-biała",
        registration_number="ZKwP-BC-21-122",
        sire_id=bc_rex.id,
        dam_id=bc_luna.id,
        description="Córka czempionów Rex × Luna.",
        available_for_breeding=False,
    )

    # GOLDEN RETRIEVER (Gdańsk)
    gr_aslan = _ensure_animal(
        farm_golden,
        name="Aslan",
        species="dog",
        breed="Golden Retriever",
        sex="male",
        birth_date=date(2016, 7, 4),
        color="Złoty",
        registration_number="ZKwP-GR-16-088",
        title="Multi-Champion",
        description="Reproduktor z linii angielskiej.",
        available_for_breeding=True,
    )
    gr_nala = _ensure_animal(
        farm_golden,
        name="Nala",
        species="dog",
        breed="Golden Retriever",
        sex="female",
        birth_date=date(2018, 8, 19),
        color="Kremowy",
        registration_number="ZKwP-GR-18-202",
        description="Suka rodzinna, świetny temperament.",
        available_for_breeding=True,
    )
    gr_simba = _ensure_animal(
        farm_golden,
        name="Simba",
        species="dog",
        breed="Golden Retriever",
        sex="male",
        birth_date=date(2021, 4, 30),
        color="Złoty",
        registration_number="ZKwP-GR-21-301",
        sire_id=gr_aslan.id,
        dam_id=gr_nala.id,
        description="Syn Aslana i Nali.",
        available_for_breeding=True,
    )

    # KONIE PÓŁKRWI (Mała Wieś)
    sw_tornado = _ensure_animal(
        farm_majka,
        name="Tornado",
        species="horse",
        breed="Polski koń półkrwi",
        sex="male",
        birth_date=date(2015, 4, 1),
        color="Kary",
        registration_number="PL-SP-2015-077",
        description="Ogier skokowy, sukcesy do klasy L.",
        available_for_breeding=True,
    )
    sw_diana = _ensure_animal(
        farm_majka,
        name="Diana",
        species="horse",
        breed="Polski koń półkrwi",
        sex="female",
        birth_date=date(2016, 6, 12),
        color="Skarogniada",
        registration_number="PL-SP-2016-101",
        description="Klacz hodowlana po linii holsztyńskiej.",
        available_for_breeding=True,
    )

    # KOTY MAINE COON (Poznań)
    mc_zeus = _ensure_animal(
        farm_koty,
        name="Zeus",
        species="cat",
        breed="Maine Coon",
        sex="male",
        birth_date=date(2019, 11, 5),
        color="Brown tabby",
        registration_number="FIFe-PL-MC-19-003",
        description="Reproduktor, waga 9 kg.",
        available_for_breeding=True,
    )
    mc_hera = _ensure_animal(
        farm_koty,
        name="Hera",
        species="cat",
        breed="Maine Coon",
        sex="female",
        birth_date=date(2020, 1, 22),
        color="Silver tabby",
        registration_number="FIFe-PL-MC-20-012",
        description="Kotka hodowlana, opiekuńcza matka.",
        available_for_breeding=True,
    )
    mc_atena = _ensure_animal(
        farm_koty,
        name="Atena",
        species="cat",
        breed="Maine Coon",
        sex="female",
        birth_date=date(2022, 5, 14),
        color="Brown tabby",
        registration_number="FIFe-PL-MC-22-021",
        sire_id=mc_zeus.id,
        dam_id=mc_hera.id,
        available_for_breeding=False,
    )

    # OWCZARKI NIEMIECKIE (Warszawa)
    on_argo = _ensure_animal(
        farm_szefa,
        name="Argo",
        species="dog",
        breed="Owczarek Niemiecki",
        sex="male",
        birth_date=date(2018, 3, 17),
        color="Czarno-podpalany",
        registration_number="ZKwP-ON-18-091",
        description="Linia pracująca, doskonała w służbie.",
        available_for_breeding=True,
    )
    on_aria = _ensure_animal(
        farm_szefa,
        name="Aria",
        species="dog",
        breed="Owczarek Niemiecki",
        sex="female",
        birth_date=date(2019, 10, 8),
        color="Czarno-podpalana",
        registration_number="ZKwP-ON-19-145",
        available_for_breeding=True,
    )

    after = (
        db.session.query(User).count()
        + db.session.query(Farm).count()
        + db.session.query(Animal).count()
    )
    return after - before
