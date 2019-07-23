from users.models import BankTransaction, ServiceSubscription


"""
Implements business logic for the membership services.

WIP!
"""
class BusinessLogic:

    # Updates the user's status based on the data in database.
    @staticmethod
    def updateuser(user):
        servicesubscriptions = ServiceSubscription.objects.filter(user=user)

        print('Updating user data for', user, 'subscriptions:', servicesubscriptions)
        for subscription in servicesubscriptions:
            print('Examining', subscription)
            skipservice = False
            if subscription.service.fullfilled_by:
                print('This service is fulfilled by', subscription.service.fullfilled_by)
                if BusinessLogic.user_is_subscribed_to(servicesubscriptions, subscription.service.fullfilled_by):
                    print('User is subscribed to ', subscription.service.fullfilled_by, ' so skipping')
                    skipservice = True
                else:
                    print('User is not subscribed to', subscription.service.fullfilled_by)
            if not skipservice:
                BusinessLogic.updatesubscription(user, subscription)

    # Updates a single subscription status for given user (used by updateuser)
    @staticmethod
    def updatesubscription(user, subscription):
        print('Updating ', subscription, 'for', user)
        if subscription.state == ServiceSubscription.SUSPENDED:
            print('Service is suspended - no action')
            return

        transactions = BankTransaction.objects.filter(user=user).order_by('date')
        if not subscription.last_payment:
            print('No previous payment - starting service')
            for transaction in transactions:
                if BusinessLogic.transaction_pays_service(transaction, subscription.service):
                    print('Transaction pays service', transaction)
                    # Todo: mark this as the first payment
                else:
                    print('Transaction does not pay service', transaction)

    # Checks if given transaction pays the service
    @staticmethod
    def transaction_pays_service(transaction, service):
        if service.cost_min and transaction.amount < service.cost_min:
            print('TA cost_min')
            return False
        if service.cost_max and transaction.amount > service.cost_max:
            print('TA cost_max')
            return False
        if not service.cost_min and transaction.amount < service.cost:
            print('TA cost')
            return False
        return True

    # Returns True if user (whose servicesubscriptions is given) is subscribed to given service
    @staticmethod
    def user_is_subscribed_to(servicesubscriptions, service):
        for subscription in servicesubscriptions:
            if subscription.service == service:
                return True
        return False
