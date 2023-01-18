from pychartjs import BaseChart,ChartType, Color, Options
from .dependencies import (monthly_records_summary_generator, year_summary_data_generator,
        all_monthly_deposits)


class MonthlyDepositsGraph(BaseChart):
    type = ChartType.Line

    class labels:
        months = [item.get('month') for item in all_monthly_deposits()]

    class data:
        data = [item.get('total') for item in all_monthly_deposits()]
        label = "Monthly Deposits"
        borderColor = Color.Green
        fill = False
        yAxisID = "all_monthly_deposits"
    class options:
        title = Options.Title("Comparison on Monthly Deposits (in Ksh.)")

        scales = {
                "yAxes" : [
                    {
                        "id" : "all_monthly_deposits",
                        "ticks" : {
                            "beginAtZero" : False,
                            }
                    }
                    ]
                }


class MonthComparisonGraph(BaseChart):
    type = ChartType.Line

    class labels:
        months = [item.get('description') for item in monthly_records_summary_generator()]

    class data:
        
        class monthly_deposits:
            data= [item.get('deposits')[0][1] for item in 
                monthly_records_summary_generator()]
            label = "Monthly Deposits"
            borderColor = Color.Red
            fill = False
            yAxisID = "comparison"
        
        class installments: 
            data= [item.get('installments')[0][1] for item in 
                monthly_records_summary_generator()]
            label = "Installments"
            borderColor = Color.Green
            fill = False
            yAxisID = "comparison"

        class supplied_loans:         
            data = [item.get('loans')[0][1] for item in 
                monthly_records_summary_generator()]
            label = "Supplied Loans"
            borderColor = Color.Brown
            fill = False
            yAxisID = "comparison"

        class loan_overdue_payments:   
            data= [item.get('overdue payments')[0][1] 
                    for item in monthly_records_summary_generator()]
            label = "Loan Overdue Payments"
            borderColor = Color.Orange
            fill = False
            yAxisID = "comparison"

        class registration_fees:        
            data = [item.get('registration fees')[0][1]
                    for item in monthly_records_summary_generator()]
            label = "Registration Fees"
            borderColor = Color.Blue
            fill = False
            yAxisID = "comparison"


        class monthly_deposit_overdue_payments:   
            data= [item.get('deposit overdue payments')[0][1] 
                    for item in monthly_records_summary_generator()]
            label = "Monthly Deposit Overdue Payments"
            borderColor = Color.Black 
            fill = False
            yAxisID = "monthly"

    class options:
        title = Options.Title("Comparison on Monthly Financial Status (in Ksh.)")

        scales = {
                "yAxes" : [
                    {
                        "id" : "monthly",
                        "ticks" : {
                            "beginAtZero" : True, 
                            },
                        "label" : "Amount in Kenyan Shillings"
                    }
                    ]
                }

class YearsComparisonGraph(BaseChart):
    type = ChartType.Line

    class labels:
        years = [item.get('financial year') for item in year_summary_data_generator()]

    class data:
        
        class monthly_deposits:
            data= [item.get('monthly deposits') for item in year_summary_data_generator()]
            label = "Monthly Deposits"
            borderColor = Color.Red
            fill = False
            yAxisID = "comparison"
        
        class installments: 
            data= [item.get('installments') for item in year_summary_data_generator()]
            label = "Installments"
            borderColor = Color.Green
            fill = False
            yAxisID = "comparison"

        class supplied_loans:         
            data= [item.get('supplied loans') for item in year_summary_data_generator()]
            label = "Supplied Loans"
            borderColor = Color.Brown
            fill = False
            yAxisID = "comparison"

        class loan_overdue_payments:   
            data= [item.get('loan overdue payments') 
                    for item in year_summary_data_generator()]
            label = "Loan Overdue Payments"
            borderColor = Color.Orange
            fill = False
            yAxisID = "comparison"

        class registration_fees:        
            data = [item.get('registration fees') 
                    for item in year_summary_data_generator()]
            label = "Registration Fees"
            borderColor = Color.Blue
            fill = False
            yAxisID = "comparison"


        class monthly_deposit_overdue_payments:   
            data= [item.get('monthly deposit overdue payments') 
                    for item in year_summary_data_generator()]
            label = "Monthly Deposit Overdue Payments"
            borderColor = Color.Black 
            fill = False
            yAxisID = "comparison"

    class options:
        title = Options.Title("Financial Year Comparisons (in Ksh.)")

        scales = {
                "yAxes" : [
                    {
                        "id" : "comparison",
                        "ticks" : {
                            "beginAtZero" : True, 
                            },
                        "label" : "Amount in Kenyan Shillings"
                    }
                    ]
                }

