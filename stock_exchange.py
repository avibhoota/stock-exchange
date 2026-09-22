"""A small in-memory limit-order exchange. All inputs are assumed valid."""

users = {}
books = {}


def reset():
    """Clear the exchange so tests or a new simulation can start fresh."""
    users.clear()
    books.clear()


def add_user(user):
    users[user] = {"cash": 0, "positions": {}}


def deposit(user, dollars):
    users[user]["cash"] += dollars


def withdraw(user, dollars):
    users[user]["cash"] -= dollars


def create_stock(company, stock, num_stocks, ipo_price):
    """Create a new company user and stock, with all shares offered for sale."""
    add_user(company)
    users[company]["positions"][stock] = num_stocks
    books[stock] = {"buy": [], "sell": [[company, num_stocks, ipo_price]]}


def order(user, side, stock, N, limit_price):
    """Return fills as [buyer, seller, quantity, price], in execution order."""
    opposite = books[stock]["sell" if side == "buy" else "buy"]
    fills = []

    while N and opposite:
        resting = opposite[0]
        other_user, remaining, price = resting
        if (side == "buy" and price > limit_price) or (
            side == "sell" and price < limit_price
        ):
            break

        quantity = min(N, remaining)
        buyer, seller = (user, other_user) if side == "buy" else (other_user, user)
        users[buyer]["cash"] -= quantity * price
        users[seller]["cash"] += quantity * price
        buyer_positions = users[buyer]["positions"]
        seller_positions = users[seller]["positions"]
        buyer_positions[stock] = buyer_positions.get(stock, 0) + quantity
        seller_positions[stock] -= quantity
        if seller_positions[stock] == 0:
            del seller_positions[stock]

        fills.append([buyer, seller, quantity, price])
        N -= quantity
        resting[1] -= quantity
        if resting[1] == 0:
            opposite.pop(0)

    if N:
        own_book = books[stock][side]
        own_book.append([user, N, limit_price])
        # Stable sorting preserves arrival priority at equal prices.
        own_book.sort(key=lambda entry: entry[2], reverse=side == "buy")

    return fills


def get_portfolio(user):
    """Return [cash, positions, pending_buys, pending_sells] as a snapshot."""
    pending_buys = {}
    pending_sells = {}
    for stock, book in books.items():
        for side, pending in (("buy", pending_buys), ("sell", pending_sells)):
            for owner, quantity, _ in book[side]:
                if owner == user:
                    pending[stock] = quantity
    return [users[user]["cash"], users[user]["positions"].copy(),
            pending_buys, pending_sells]
