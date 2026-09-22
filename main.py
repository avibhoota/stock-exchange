"""Read one exchange command per line and print fills or portfolios."""

import sys

import stock_exchange as exchange


def main():
    for line in sys.stdin:
        parts = line.split()
        if not parts:
            continue
        command, *args = parts
        if command == "add_user":
            exchange.add_user(args[0])
        elif command == "deposit":
            exchange.deposit(args[0], int(args[1]))
        elif command == "withdraw":
            exchange.withdraw(args[0], int(args[1]))
        elif command == "create_stock":
            exchange.create_stock(args[0], args[1], int(args[2]), int(args[3]))
        elif command == "order":
            user, side, stock, quantity, price = args
            for buyer, seller, quantity, price in exchange.order(
                user, side, stock, int(quantity), int(price)
            ):
                print(buyer, seller, stock, quantity, price, flush=True)
        elif command == "get_portfolio":
            cash, positions, buys, sells = exchange.get_portfolio(args[0])
            print("CASH", cash, flush=True)
            for stock, quantity in positions.items():
                print(stock, quantity, flush=True)
            for stock, quantity in buys.items():
                print(stock, quantity, "PENDING_BUY", flush=True)
            for stock, quantity in sells.items():
                print(stock, quantity, "PENDING_SELL", flush=True)


if __name__ == "__main__":
    main()
