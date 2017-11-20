from __future__ import print_function

from strategies.order.OrderStatus import OrderStatus


class MakeOrder:
    def __init__(self, tax=0.001, commission=0.0003):
        self.tax = tax
        self.commission = commission

    def order_buy(self, current_bar, execution_price, quantity, asset, stock_in_hand):
        usable_asset = self.compute_usable_asset(asset, stock_in_hand)

        if usable_asset < execution_price * quantity:
            print('[%s]price reach at: %.2f, '
                  'execution price at: %.2f , '
                  'trigger action: BUY , '
                  'current total asset: %.2f, '
                  'current usable asset: %.2f, '
                  'no enough asset, do not make order' % (
                current_bar.datetime, current_bar.close, execution_price, asset, usable_asset))

            return OrderStatus.FAIL, asset, stock_in_hand
        else:
            return self.execute_buy(current_bar, execution_price, quantity, asset, stock_in_hand)

    def order_sell(self, current_bar, execution_price, quantity, asset, stock_in_hand):
        history_stock = [stock for stock in stock_in_hand if stock['datetime'] < current_bar.datetime.replace(hour=0)]
        total_quantity = sum([stock['quantity'] for stock in history_stock])

        if total_quantity < quantity:
            print('[%s]price reach grid at: %.2f, '
                  'execution price at: %.2f , '
                  'trigger action: SELL, '
                  'current total asset: %.2f, '
                  'no enough yesterday position, do not make order' % (
                      current_bar.datetime, current_bar.close, execution_price, asset))

            return OrderStatus.FAIL, asset, stock_in_hand, 0
        else:
            return self.execute_sell(current_bar, execution_price, quantity, asset, stock_in_hand)

    def execute_buy(self, current_bar, execution_price, no_of_stock, asset, stock_in_hand):
        asset = asset - self.charge_commission(execution_price, no_of_stock)

        stock_in_hand.append({'price': execution_price, 'quantity': no_of_stock, 'datetime': current_bar.datetime})

        print('[%s]price reach at: %.2f, '
              'execution price at: %.2f , '
              'trigger action: BUY , '
              'current total asset: %.2f, '
              'make order' % (current_bar.datetime, current_bar.close, execution_price, asset))

        print(*stock_in_hand, sep='\n')

        return OrderStatus.SUCCESS, asset, stock_in_hand

    def execute_sell(self, current_bar, execution_price, quantity, asset, stock_in_hand):
        asset = asset - self.charge_commission(execution_price, quantity)

        profit = 0
        index = 0
        for i in range(len(stock_in_hand)):
            if quantity - stock_in_hand[i]['quantity'] >= 0:
                profit = profit + (execution_price - stock_in_hand[i]['price']) * stock_in_hand[i]['quantity']
                quantity = quantity - stock_in_hand[i]['quantity']
                index = i + 1
                if quantity == 0:
                    break
            else:
                profit = profit + (execution_price - stock_in_hand[i]['price']) * quantity
                stock_in_hand[i]['quantity'] = stock_in_hand[i]['quantity'] - quantity
                break

        stock_in_hand = stock_in_hand[index:]

        if profit > 0:
            profit = profit * (1 - self.tax)
            asset = asset + profit
        else:
            asset = asset + profit

        print('[%s]price reach at: %.2f, '
              'execution price at: %.2f , '
              'trigger action: SELL, '
              'current total asset: %.2f, '
              'make order' % (current_bar.datetime, current_bar.close, execution_price, asset))

        print(*stock_in_hand, sep='\n')

        return OrderStatus.SUCCESS, asset, stock_in_hand, profit

    def charge_commission(self, price, quantity):
        return max(price * quantity * self.commission, 5)

    @staticmethod
    def compute_usable_asset(asset, stock_in_hand):
        sum = 0
        for stock in stock_in_hand:
            sum = sum + stock['quantity'] * stock['price']
        return asset - sum
