import threading, os, flask, time
from faker import Faker
from random import randint
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from . import db, create_app
from .models import (user, member, occupation, document_type, month, loan_type, role,
        registration_fee, employer, employment, monthly_deposit, phone_number, review,
        branch, event, event_image, loan_overdue, loan_overdue_payment, loan, installment,
        monthly_deposit_overdue, deposit_overdue_payment, group)

class Timer:
    """
    class Timer
        Generates a new time between begin and end
        begin is the time to start from, default is datetime.utcnow()
        end is the time to stop, default is datetime.utcnow()
    """
    current = list()

    def __init__(self, begin = datetime.utcnow(), end = datetime.utcnow()):
        # set the initial time
        try:
            with open('app/file.txt', 'r') as file:
                self.begin = datetime.strptime(file.read(), "%d-%b-%Y %H:%M:%S.%f")
        except:
            self.begin = datetime.utcnow() - timedelta(days = 5 * 365, seconds = 0, milliseconds = 0)

        self.end = end
        self.days = 1 #number of days from self.begin
        self.seconds = 1000 #number of self.days + seconds from begin
        self.milliseconds = 1000 # number of self.days + seconds + milliseconds from begin
        self.seed = 1

        # get time to begin from file
        try:
            file = open('file.txt', 'r')
            file.read()
        except:
            with open('file.txt', 'r') as file:
                file.write(self.begin)

    def add(self, brake = 1):
        """
        add()
            Generates a new datetime.datetime object later than previous one
            returns datetime.datetime object
            brake is a time generation regulator - reduces time difference
        """
        self.seconds = randint(self.seconds, 
                self.seconds + int(randint(10000, 100000)/brake))

        self.milliseconds = randint(self.milliseconds, 
                self.milliseconds + int(10000000/brake))

        jump = timedelta(days = self.days, seconds = self.seconds, 
                milliseconds = self.milliseconds)

        self.current = self.begin + jump
        
        with open('app/file.txt', 'w') as file:
            file.write((self.begin + jump).strftime("%d-%b-%Y %H:%M:%S.%f"))
        
        return self.today()


    def today(self):
        """Returns current Timer date and time"""
        with open('app/file.txt', 'r') as file:
            try:
                return datetime.strptime(file.read(), "%d-%b-%Y %H:%M:%S.%f")
            except:
                print("Option 2")
                return self.current

    def reset(self):
        """Resets Timer attributes to default"""
        self.days = 1
        self.seconds = 1000
        self.milliseconds = 1000
        self.seed = 1


class Thread(threading.Thread):
    def __init__(self, action):
        super().__init__(target = action)
        
        self.app = create_app('development')
        self.action = action

        with self.app.app_context():
            self.start()


class Generator:
    def __init__(self, locale = 'en_CA', period = 5, fee = 2000):
        self.period = timedelta(days = (period * 365)+100, seconds = 0, milliseconds = 0)
        self.begin = datetime.utcnow() - self.period #default is 5 years from current date

        self.fake = Faker(locale = locale)
        self.timer = Timer(begin = self.begin, end = datetime.utcnow())

        self.maximum_registration_fee = fee #maximum registration fee
    
    def reset_timer(self):
        """
        reset_timer()
            resets timer to default values

        """
        self.timer.reset()

    def month_generator(self, date = datetime.utcnow()):
        description = date.strftime("%B %Y")
        return description

    def generate_group(self):
        """
        generate_group
            generates a group consisting of randomly selected members
        """
        maximum_members = randint(5, 10)
        fake_time = self.timer.add(1000)
        
        Group = group(
                name = self.fake.company(),
                email_address = self.fake.email(),
                phone_no = self.fake.phone_number(),
                location_address = self.fake.address(),
                date_created = fake_time,
                last_updated = fake_time)
        
        db.session.add(Group)
        db.session.commit()
        print('Group created successfully...')

        #assign members to the newly created group
        Group = group.query.order_by(group.group_id.desc()).first() #latest group created

        #query [maximum_members] members from the database without groups; latest members
        members = member.query.filter_by(group_id = None).order_by(member.member_id.desc()).limit(maximum_members)
        for member_item in members:
            fake_time = self.timer.add(800)
            
            member_item.group_id = Group.group_id
            member_item.last_updated = fake_time
            
            db.session.add(member_item)
            print(f'member ID {member_item.member_id} added successfully to group {Group.name} ...')
        db.session.commit()


    def pay_overdue_monthly_deposits(self):
        """
        pay_overdue_monthly_deposits
            generates payments of overdue monthly deposits
        """
        overdues = monthly_deposit_overdue.query.filter_by(status = 'pending').all()

        # ensure all overdue installment payments are made
        for overdue in overdues:
            paid = db.session.query(func.sum(deposit_overdue_payment.amount))\
                    .filter_by(monthly_deposit_overdue_id = overdue.monthly_deposit_overdue_id).scalar()
            if not paid:
                paid = 0 #scalar return a numerical value or None

            if paid < flask.current_app.config['DEPOSIT_OVERDUE']:
                while True:
                    random_amount = randint(1, 10) * 100
                    if random_amount <= (flask.current_app.config['DEPOSIT_OVERDUE'] - paid):
                        fake_time = self.timer.add(10000)
                        payment = deposit_overdue_payment(
                                amount = random_amount,
                                monthly_deposit_overdue_id = overdue.monthly_deposit_overdue_id,
                                date_created = fake_time,
                                last_updated = fake_time)
                        db.session.add(payment)

                        if ((flask.current_app.config['DEPOSIT_OVERDUE'] - paid) - random_amount) == 0:
                            overdue.status = 'paid'
                            db.session.add(overdue)
                            db.session.commit()
                            print('Overdue monthly deposit charge payment successful...')
                            break; #a payment has been made
                        
                        db.session.commit()
                        print('Overdue monthly deposit charge payment successful...')


    def generate_overdue_monthly_deposits(self):
        """
        generate_overdue_monthly_deposits
            automates generation of deferred monthly deposit payments alongside those below the given limit
        """
        months = month.query.all()
        for member_item in member.query.all():
            for month_item in months:
                if member_item.date_created < datetime.strptime(month_item.description, '%B %Y'):
                    #check whether ther is an existing overdue record for member for month, month_item
                    overdues = monthly_deposit_overdue.query.filter(
                            monthly_deposit_overdue.member_id == member_item.member_id,
                            monthly_deposit_overdue.month_id == month_item.month_id).first()
                    if overdues:
                        continue #a record already exists; no need to continue with process

                    #check whether member in question has made any deposit for the month
                    deposits = db.session.query(func.sum(monthly_deposit.amount))\
                        .filter(
                            monthly_deposit.month_id == month_item.month_id,
                            monthly_deposit.member_id == member_item.member_id).scalar()
                    if not deposits:
                        deposits = 0

                    if (deposits == 0) or (deposits < flask.current_app.config['DEPOSIT_OVERDUE']):
                        fake_time = self .timer.add(10000)
                        overdue = monthly_deposit_overdue(
                                amount = flask.current_app.config['DEPOSIT_OVERDUE'] - deposits,
                                month_id = month_item.month_id,
                                member_id = member_item.member_id,
                                date_created = fake_time,
                                last_updated = fake_time)
                        db.session.add(overdue)
                        print(f'Generation of overdue monthly deposit for ID {member_item.member_id} - {month_item.description}')
        db.session.commit()
        return None


    def generate_event(self, year = datetime.utcnow().strftime("%Y")):
        """
        generate_event
            registers event
            year is when the event was held
        """
        description = f"Annual General Meeting (AGM) July {year} - Members' Dinner"
        
        Event = event(description = description)
        db.session.add(Event)
        try:
            db.session.commit()
            print("Generation of event successful...")

            try:
                os.mkdir(
                    os.path.join(flask.current_app.config['GALLERY_UPLOAD_PATH'],
                        description.strip()))
            except:
                pass

        except IntegrityError:
            db.session.rollback()

    def generate_installment(self, loan_id):
        """
        generate_installment(loan_id)
            generates installment record for loan ID, loan_id
            loan_id is the ID for loan of which installment is generated
        """
        Loan = loan.query.filter_by(loan_id = loan_id).first()
        
        paid = db.session.query(func.sum(installment.amount))\
                .filter_by(loan_id = loan_id).scalar()
        if not paid:
            paid = 0

        if Loan:
            random_amount = randint(1, 200) * 100
            fake_time = self.timer.add(700)
            if random_amount <= (Loan.amount - paid):
                Installment = installment(
                    amount = random_amount,
                    loan_id = loan_id,
                    date_created = fake_time,
                    last_updated = fake_time
                )
                db.session.add(Installment)
                if (Loan.amount - (paid + random_amount)) == 0:
                    Loan.status = 'Paid'
                    Loan.last_updated = fake_time
                    db.session.add(Loan)

                db.session.commit()
                print("Generation of loan installment successful...")


    def generate_loan_overdue_payment(self, loan_overdue_id):
        """
        generate_loan_overdue_payment(loan_overdue_id)
            generates payment record for loan overdue ID, loan_overdue_id
        """
        Loan_Overdue = loan_overdue.query.filter_by(
                loan_overdue_id = loan_overdue_id).first()

        paid = db.session.query(func.sum(loan_overdue_payment.amount))\
                .filter_by(loan_overdue_id = loan_overdue_id).scalar()
        if not paid:
            paid = 0

        random_amount = randint(10, 500) * 10
        fake_time = self.timer.add(10000)

        if random_amount <= (Loan_Overdue.amount - paid):
            payment = loan_overdue_payment(
                amount = random_amount,
                loan_overdue_id = loan_overdue_id,
                date_created = fake_time,
                last_updated = fake_time
            )
            db.session.add(payment)
            if (Loan_Overdue.amount - (paid + random_amount)) == 0:
                Loan_Overdue.status = "Paid"
                Loan_Overdue.last_updated = fake_time
                db.session.add(Loan_Overdue)

            db.session.commit()
            print("Generation of loan overdue payment successful...")


    def generate_loan_overdue(self, Loan = None, description = ''):
        """
        generate_loan_overdue(loan_id)
            generates loan_overdue record for defaulted loan ID, loan_id
            Loan is the loan which is defaulted
            description is the title of the month for which loan overdue record is added
        """
        record = loan_overdue.query.filter(
                loan_overdue.month == description,
                loan_overdue.loan_id == Loan.loan_id
            ).first()
        
        Loan = loan.query.filter_by(loan_id = Loan.loan_id).first()
        if not record:
            fake_time = self.timer.add(10000)
            Loan_Overdue = loan_overdue(
                amount = int((10/100) * Loan.amount),
                loan_id = Loan.loan_id,
                month = description,
                date_created = fake_time,
                last_updated = fake_time
            )
            db.session.add(Loan_Overdue)
            db.session.commit()
            print("Generation of loan overdue record successful...")


    def generate_loan(self, member_id = 1, type_id = 1):
        """
        generate_loan(member_id, type_id)
            generates individual loan of a random principal for member ID, member_id
            member_id is the ID for member for whom loan is generated
        """
        viable = True #By default member is viable for loan
        for item in loan.query.filter_by(member_id = member_id).all():
            if item.status == 'pending':
                viable = False

        Loan_Type = loan_type.query.filter_by(loan_type_id = type_id).first()
        
        deposits = db.session.query(func.sum(monthly_deposit.amount))\
                .filter_by(member_id = member_id).scalar()

        if deposits and viable:
            fake_time = self.timer.add()
            Loan = loan(
                loan_type = Loan_Type.loan_type_id,
                amount = (deposits/2.0) * Loan_Type.multiplier,
                member_id = member_id,
                date_created = fake_time,
                last_updated = fake_time
            )
            db.session.add(Loan)
            db.session.commit()
            print("Generation of loan successful...")


    def generate_review(self, key = None, data = {}):
        """
        generate_review(key, data)
            generates review based on values from a  dictionary, data
            data is a dictionary containing desired data
            key is the key to be used with data.get(key)
        """
        fake_time = self.timer.add(10)
        if data.get(key):
            Review = review(
                member_id = key,
                description = data.get(key),
                date_created = fake_time,
                last_updated = fake_time
            )
            db.session.add(Review)
            db.session.commit()

    def generate_monthly_deposit(self, month_id = None, member_id = None):
        """
        generate_monthly_deposit(month_id)
            generates a random amount for monthly deposit of month ID, month_id
            month_id is the ID of the month whose deposit is generated
            member_id is the ID of the member for whom the deposit is made
        """
        fake_time = self.timer.add(20)
        random_amount = randint(50, 100)
        deposit = monthly_deposit(
            amount = random_amount * 100,
            member_id = member_id,
            month_id = month_id,
            date_created = fake_time,
            last_updated = fake_time
        )
        db.session.add(deposit)
        db.session.commit()
        print("Generation of monthly deposit successful...")


    def generate_branch(self):
        """
        generate_branch()
            generates branch for the organization
        """
        fake_time = self.timer.add(10000)
        Branch = branch(
            town = self.fake.city(),
            location_address = self.fake.address(),
            email_address = self.fake.email(),
            phone_no = self.fake.phone_number(),
            date_created = fake_time,
            last_updated = fake_time
        )
        db.session.add(Branch)
        try:
            db.session.commit()
            print("Generation of branch successful...")
        
        except:
            db.session.rollback()


    def generate_phone_number(self, member_id):
        """
        generate_phone_number(member_id)
            generates phone number for member with member ID member id and add to database
            member_id is the ID for the member for whom phone number is generated
        """
        fake_time = self.timer.add(200)
        phone_no = phone_number(
                member_id = member_id,
                phone_no = "07" + str(randint(10000000, 99999999)),
                date_created = fake_time,
                last_updated = fake_time
        )
        db.session.add(phone_no)
        try:
            db.session.commit()
            print("Generation of phone number successful...")

        except IntegrityError:
            db.session.rollback()


    def generate_profile_image(self, person):
        """
        generate_member_image(person)
            randomly selects image avatars from a designated folder and assigns to person
            person is either a member or a user
        """
        male_images = [image for image in os.listdir("Image-Repository/male")]
        female_images = [image for image in os.listdir("Image-Repository/female")]

        if person.gender == "male":
            person.associated_image = male_images[randint(1, len(male_images) - 1)]
        else:
            person.associated_image = female_images[randint(1, len(female_images) - 1)]
        
        fake_time = self.timer.add(200)
        person.last_updated = fake_time
        
        db.session.add(person)
        db.session.commit()
        print("Generation of profile image successful...")


    def generate_loan_type(self, item = {}):
        """
        generate_loan_type(item)
            generates loan type based on the dictionary provided, loan_type
            item is a dictionary containing data required for generation
        """
        fake_time = self.timer.add(10000)
        Loan_Type = loan_type(
            description = item.get('description'),
            max_period = item.get("max_period"),
            multiplier = item.get("multiplier"),
            overdue_penalty = item.get("overdue_penalty"),
            rate = item.get("rate"),
            date_created = fake_time,
            last_updated = fake_time
        )
        db.session.add(Loan_Type)
        try:
            db.session.commit()
            print("Generation of loan type successful...")

        except:
            db.session.rollback()

    def generate_month(self, description = ''):
        """
        generate_month(description)
            generates month records for monthly deposits and adds them to the database
            description is the title of the month
        """
        
        Month = month(description = description)
        
        db.session.add(Month)
        try:
            db.session.commit()
            print("Month added successfully...")
        except:
            db.session.rollback()

        self.generate_event(self.timer.today().strftime("%Y"))
        self.generate_overdue_monthly_deposits()


    def generate_document_type(self, description = ''):
        """
        generate_document_type(description)
            generates document type records and saves in database
            description is the title of the document type
        """
        fake_time = self.timer.add(10000)

        Document_Type = document_type(
                description = description,
                date_created = fake_time,
                last_updated = fake_time
                )

        db.session.add(Document_Type)
        try:
            db.session.commit()
            print("Generation of document type successful...")

        except:
            db.session.rollback()

    def generate_employment(self, member_id):
        """
        generate_employment()
            generates employment for member ID, member_id
            member_id is the member for whom employment is generated
        """
        #acquire the number of records available for occupations and employers
        occupations = db.session.query(func.count(occupation.description)).scalar()
        employers = db.session.query(func.count(employer.name)).scalar()

        fake_time = self.timer.add(500)
        Employment = employment(
                member_id = member_id,
                employer_id = randint(1, employers),
                occupation_id = randint(1, occupations),
                date_created = fake_time,
                last_updated = fake_time
                )
        db.session.add(Employment)
        db.session.commit()
        print("Generation of employment record successful...")

    def generate_employer(self):
        """generates employer records"""
        fake_time = self.timer.add(900)
        Employer = employer(
                name = self.fake.company(),
                location_address = self.fake.address() + "\n" + self.fake.city(),
                email_address = self.fake.email(),
                phone_no = self.fake.phone_number(),
                date_created = fake_time,
                last_updated = fake_time
                )
        db.session.add(Employer)
        try:
            db.session.commit()
            print("Generation of employer successful...")

        except IntegrityError:
            db.session.rollback()
            self.generate_employer() #try again
    
    def generate_occupation(self):
        """generates occupations"""
        fake_time = self.timer.add(1000)
        Occupation = occupation(
                description = self.fake.job(),
                date_created = fake_time,
                last_updated = fake_time
                )
        try:
            db.session.add(Occupation)
            db.session.commit()
            print("Generation of occupation successful...")

        except IntegrityError:
            db.session.rollback()


    def generate_registration_fee(self, member_id):
        """
        generate_registration_fee()
            Generates registration fee with a random amount for member ID, member_id
            member_id is the id number of member for whom fee is paid for
        """
        #get amount already paid by member
        paid = db.session.query(func.sum(registration_fee.amount))\
                .filter_by(member_id = member_id).scalar()
        if not paid:
            paid = 0 #if no record available

        #if member has not completed payment to the maximum amount
        if paid < self.maximum_registration_fee:

            successful = False #generation failed by default        
            while not successful:
                amount = randint(15, 20) * 100

                #registration fee amount cannot exceed maximum
                if amount <= (self.maximum_registration_fee - paid):
                    fake_time = self.timer.add(1000)
                    Fee = registration_fee(
                            amount = amount, 
                            member_id = member_id,
                            date_created = fake_time,
                            last_updated = fake_time)
                    db.session.add(Fee)
                    db.session.commit()
                    
                    successful = True #success
                    print("Generation of registration fee successful...")


    def generate_member(self, generate_fee = True, generate_job = True):
        """
        generate_member()
            Populates details on member and adds them into the database
            generate_fee is a switch that regulates generation of registration fees
        """
        Member = member()

        #generate member attributes
        Member.first_name = self.fake.first_name()
        Member.middle_name = self.fake.last_name()
        Member.last_name = self.fake.last_name()
        Member.email_address = self.fake.email()
        Member.location_address = self.fake.address() + "\n" + self.fake.city()
        Member.id_no = randint(500306778, 500393939)

        fake_time = self.timer.add()
        print(fake_time)
        Member.date_created = fake_time
        Member.last_updated = fake_time
        
        #generate a realistic date
        while True:
            fake_date = self.fake.date_of_birth()

            if fake_date >= date(1976, 1, 1) and fake_date <= date(1997, 12, 12):
                Member.date_of_birth = fake_date
                break

        #randomly generate gender of user
        random_integer = randint(1, 11)
        Member.gender = "male" if random_integer % 2 == 0 else "female"

        Member.nationality = "Canada"
        Member.status = "activated"

        #save to the database
        db.session.add(Member)
        try:
            db.session.commit()
            print("Generation of member successful...")

            #generate profile image
            Member = member.query.filter_by(email_address = Member.email_address).first()
            if generate_fee:
                self.generate_registration_fee(Member.member_id)

            if generate_job:
                self.generate_employment(Member.member_id)
                self.generate_phone_number(Member.member_id)
                self.generate_profile_image(Member)

            self.generate_month(
                self.month_generator(self.timer.today())
            )
            current_month = self.month_generator(self.timer.today())
            Month = month.query.filter_by(description = current_month).first()
            self.generate_monthly_deposit(Month.month_id)

        except IntegrityError as e:
            db.session.rollback()



    def generate_user(self):
        """
        generate_user()
            Populates details on user and adds them into the database
        
        """
        User = user()
        User.first_name = self.fake.first_name()
        User.middle_name = self.fake.last_name()
        User.last_name = self.fake.last_name()
        User.email_address = self.fake.email()
        User.location_address = self.fake.address() + "\n" + self.fake.city()
        User.id_no = randint(500306778, 500393939)

        filtered_roles = ['Guest', 'Member', 'Group Member']
        permitted_roles = [item.role_id for item in role.query.all() 
                if item.name not in filtered_roles]

        User.role_id = permitted_roles[randint(0, len(permitted_roles) - 1)]

        fake_time = self.timer.add()
        print(fake_time)
        User.date_created = fake_time
        User.last_updated = fake_time

        #generate a realistic date
        while True:
            fake_date = self.fake.date_of_birth()

            if fake_date >= date(1976, 1, 1) and fake_date <= date(1997, 12, 12):
                User.date_of_birth = fake_date
                break

        #randomly generate gender of user
        random_integer = randint(1, 11)
        User.gender = "male" if random_integer % 2 == 0 else "female"
        User.nationality = "Canada"
        User.password = "password"

        #save to the database
        db.session.add(User)
        try:
            db.session.commit()
            print("Generation of User Successful...")

            #generate profile image
            User = user.query.filter_by(email_address = User.email_address).first()
            self.generate_profile_image(User)

        except IntegrityError:
            db.session.rollback()


class App:
    def __init__(self, reviews = {}, document_types = [], loan_types = []):
        self.generator = Generator(locale = "en_CA")
        
        self.reviews = reviews
        self.loan_types = loan_types
        self.document_types = document_types

    def initialize_system(self):
        #initialization
        db.drop_all()
        db.create_all()
        
        role.insert_roles()

        #auto generation
        self.generator.generate_branch()
        for i in range(randint(20, 25)):
            self.generator.generate_user()

        for i in self.document_types:
            self.generator.generate_document_type(i)

        for i in self.loan_types:
            self.generator.generate_loan_type(i)
        
        for i in range(10):
            self.generator.generate_employer()
            self.generator.generate_occupation()
            self.generator.generate_month(
                    self.generator.month_generator(self.generator.timer.today())
                )

        for i in range(5):
            self.generator.generate_member()

        self.sleeping_thread()

    def sleeping_thread(self):
        # retrieve last value of count
        try:
            with open() as file:
                count = int(file.read())
        except:
            count = 1

        # retrieve last value of multiplier
        try:
            with open() as file:
                multiplier = int(file.read())
        except:
            multiplier = 0

        # a loop for all data
        while True:
            if count % 20 == 0:
                self.generator.generate_group()
            
            if count == 34:
                for key in self.reviews.keys():
                    self.generator.generate_review(key, self.reviews)
            
            new = 0
            with open("new.txt", "w") as file:
                file.write(str(count))

            # let us generate a new branch based on number of iterations
            if count in (50, 100, 150, 200, 400):
                self.generator.generate_branch()
                
                # a branch must have new users
                for i in range(randint(20, 25)):
                    self.generator.generate_user()
            
            for i in range(5):
                # generate new month
                self.generator.generate_month(
                    self.generator.month_generator(self.generator.timer.today())
                )

                # generate loan installments
                loans = loan.query.all()
                if loans:
                    for i in range(len(loans)):
                        self.generator.generate_installment(loan_id = randint(1, len(loans)))

                if range(multiplier):
                    #generate new member
                    self.generator.generate_member()
                    new += 1
                    
                    # generate new employer
                    self.generator.generate_employer()

                    # generate new month
                    self.generator.generate_month(
                            self.generator.month_generator(self.generator.timer.today())
                        )

                    # find the numbre of deposits for current month
                    deposits = db.session.query(func.count(monthly_deposit.deposit_id))\
                        .filter_by(month_id = self.generator.month_generator(
                            self.generator.timer.today()
                        )
                    ).scalar()

                    # find the total number of registered members
                    members = db.session.query(func.count(member.member_id)).scalar()

                    # are deposits less than number of twice the number of members?
                    if not deposits or (deposits <= members * 2):
                        for i in range(members - new):
                            # ensure that we are still in the current month
                            self.generator.generate_month(
                                self.generator.month_generator(
                                    self.generator.timer.today())
                            )

                            # let us retrieve what month we are in
                            current_month = self.generator.month_generator(
                                self.generator.timer.today())
                            
                            # let us retrieve our financial month
                            Month = month.query.filter_by(description = current_month)\
                                    .first()

                            # let us generate a monthly deposit
                            self.generator.generate_monthly_deposit(
                                month_id = Month.month_id, member_id = randint(1,members))
                    else:
                        # let us pass time
                        self.generator.timer.add()

                # generate occupation
                self.generator.generate_occupation()

            members = 0
            complete = False
            while not complete:
                # retrieve all loans
                loans = loan.query.join(
                    loan_type, loan_type.loan_type_id == loan.loan_type)\
                        .add_columns(
                            loan.loan_id,
                            loan.date_created,
                            loan_type.max_period
                        ).all()

                # iterate through the loans
                for Loan in loans:
                    # calculate the maximum period
                    max_period = timedelta(
                        days = (Loan.max_period * 365), seconds = 0, milliseconds = 0)
                    current_period = self.generator.timer.today() - Loan.date_created

                    # has the loan exceeded it's time limit
                    if current_period >= max_period:

                        # let us generate a loan overdue
                        self.generator.generate_loan_overdue(
                            Loan = Loan, description = self.generator.month_generator(
                                self.generator.timer.today()
                                )
                            )

                # let us keep ensuring our financial month is updated
                self.generator.generate_month(
                    self.generator.month_generator(self.generator.timer.today())
                )

                # some monthly deposits are overdue...let us generate them
                self.generator.generate_overdue_monthly_deposits()

                # some people wanna clear their overdue monthly deposits
                self.generator.pay_overdue_monthly_deposits()

                # we want this section done randomly
                if randint(1, 10) % 2 == 0:
                    # retrieve number of overdue loans
                    loan_overdues = db.session.query(
                            func.count(loan_overdue.loan_overdue_id)
                        ).scalar()

                    if loan_overdues >= 2:
                        for i in range(loan_overdues * 30):
                            self.generator.generate_loan_overdue_payment(
                                    randint(1, loan_overdues)
                            )

                    # distribute a loan randomly
                    members = db.session.query(func.count(member.member_id)).scalar()
                    self.generator.generate_loan(member_id = randint(1, members))

                    # let us pay some loan installments
                    loans = db.session.query(func.count(loan.loan_id)).scalar()
                    if loans:
                        for i in range(loans):
                            self.generator.generate_installment(
                                    loan_id = randint(1, loans)
                                    )
                
                members += 1
                if members >= randint(15, 20):
                    complete = True

            count += 1
            multiplier += 1

def stage_one(start = False):
    document_types = ['Passport', 'National ID Card', 'Military ID Card',
            'Birth Certificate', 'Driver License']

    loan_types = [
            {
                'description' : 'Individual Loan',
                'rate' : 1.2,
                'max_period' : 3,
                'multiplier' : 3,
                'overdue_penalty' : 10
            },
            {
                'description' : 'Group Member Loan',
                'rate' : 1,
                'max_period' : 4,
                'multiplier' : 4,
                'overdue_penalty' : 10
            },
            {
                'description' : 'Group Loan',
                'rate' : 0.8,
                'max_period' : 5,
                'multiplier' : 3,
                'overdue_penalty' : 10
                }
            ]
    reviews = {
            34 :
            """I have gained financial stability, thanks to the low interest rate loans
            offered by the organization. All I can say is 'asante'.""",
            78 :
            """Being a member has benefited me greatly. I have been able to
            establish my self financially. Nevertheless, I have been able to invest in
            real estate, thanks to this organization.""",
            77 :
            """
            Top notch staff, reputable hospitality alongside affordable financial aids is
            all I needed to attain financial growth. To all non-members, I urge you to
            take a step towards growth and development by becoming a member.
            """
    }
    app = App(reviews = reviews, document_types = document_types, loan_types = loan_types)

    # start from where we left
    if not start:
        app.sleeping_thread()
    else:
        # initialize the system
        app.initialize_system()


if __name__ == '__main__':
    print("Run script from shell via $flask shell command")

