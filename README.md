# Simple stock exchange

A stock exchange brings buyers and sellers together to trade shares in
companies. This project models the basic process: users hold cash and shares,
submit orders, and exchange cash for shares when their prices are compatible.

The exchange supports **limit orders**. A buyer specifies the most they will pay
per share, and a seller specifies the least they will accept. Each stock has an
**order book** containing orders that have not yet filled. When a new order
arrives, the exchange matches it against the best available prices on the other
side, giving earlier orders priority at equal prices. A **fill** is an executed
trade; an order may produce several fills, with any unfilled shares remaining
pending in the book.

For example, if a seller has offered shares at $10 and a buyer arrives willing
to pay up to $12, they trade at $10: this exchange uses the existing order's
price. The buyer receives shares and the seller receives cash.

## Supported functionality

- Create users, deposit cash, and withdraw cash.
- Introduce a stock through a simplified IPO: create a company account, give it
  an initial supply of shares, and offer those shares for sale at the IPO price.
- Buy and sell shares using limit orders, including resale by shareholders.
- Match orders by price and arrival time, supporting partial fills and orders
  that trade with multiple counterparties.
- View each user's cash, share holdings, pending buys, and pending sells.
- Use the exchange as a Python module or through line-based stdin/stdout.

The goal is to keep the mechanics easy to read and test. The model assumes valid
inputs and sufficient cash and shares, uses integers throughout, and does not
reserve balances for pending orders. There are no market orders, cancellations,
fees, or saved state. The detailed assumptions appear below.

## Project layout

Python 3 is the only requirement; there are no third-party dependencies or
classes. `stock_exchange.py` contains reusable functions and in-memory state;
`main.py` reads commands and prints results. This README contains the usage
guide and executable tests. Each new process starts with an empty exchange.

## Run

From this directory:

```sh
python3 main.py
```

Enter one command per line; end input with EOF (Ctrl-D on macOS/Linux). You can
also use `python3 main.py < commands.txt`. Names and symbols are single tokens.
Blank lines are ignored. No prompts, headings, or success messages are printed.

| Command | Behavior |
| --- | --- |
| `add_user user` | Create a user with zero cash and no shares. |
| `deposit user dollars` | Add cash. |
| `withdraw user dollars` | Remove cash. |
| `create_stock company stock num_stocks ipo_price` | Create a new company user with zero cash, give it all the shares, and place the initial sell order. |
| `order user buy\|sell stock N limit_price` | Match an order and print one line per fill. |
| `get_portfolio user` | Print cash, held shares, pending buys, and pending sells. |

Only `order` and `get_portfolio` produce output. A fill is printed as
`buyer seller stock quantity price`. An order with no fills prints nothing.
Portfolio lines are `CASH amount`, `stock quantity`,
`stock quantity PENDING_BUY`, or `stock quantity PENDING_SELL`.
Holdings and pending quantities appear on separate lines. Zero positions are
omitted. Ordering within each portfolio section is unspecified; there is no
separator between successive command results.

Example input:

```text
create_stock IBM_CO IBM 100 10
add_user alice
deposit alice 1000
order alice buy IBM 20 12
get_portfolio alice
get_portfolio IBM_CO
```

Output:

```text
alice IBM_CO IBM 20 10
CASH 800
IBM 20
CASH 200
IBM 80
IBM 80 PENDING_SELL
```

## Rules and simplifying assumptions

- Only limit orders; no cancellation or modification.
- All quantities, prices, deposits, and withdrawals are positive integers.
  Cash and prices use the same whole-dollar units. No fees or fractional shares.
- Inputs are valid; there is no error checking. Users exist before use.
  New usernames are unique. `create_stock` introduces both a new company
  username and a new stock symbol. Orders come after stock creation.
- Each user has at most one pending order per stock, across both sides.
  It must fill completely before that user places another order for that stock.
  Different stocks may have pending orders simultaneously.
- Cash and shares are never reserved. Callers ensure sufficient cash and shares
  at each fill and withdrawal, including across multiple pending orders.
  Borrowing and short selling are outside the model.
- Buy orders have highest-price priority; sell orders have lowest-price
  priority. Equal prices use arrival order, preserved by stable list sorting.
- A buy limit must be at least the sell limit to match. Each fill uses the
  existing (resting) order's price, regardless of which side arrives next.
- An incoming order matches directly against the opposite book, possibly
  creating multiple fills. Only its unfilled remainder enters its own book.
- Each fill transfers quantity times price from buyer to seller and transfers
  the shares from seller to buyer. Pending orders alone change neither balance.
- Unsold IPO shares remain held by the company and listed as pending sells.
  Stock books remain present even when empty. The one-order rule prevents
  self-trading for valid inputs.

## Python interface and state

The Python functions have the same arguments as the commands, with integer
numeric arguments. Mutating functions return `None`, except `order`, which
returns a list of `[buyer, seller, quantity, price]` fills in execution order
(or `[]`). The stock is supplied by the caller, so it is omitted from each
returned fill and included by `main.py` when printing.

`get_portfolio(user)` returns `[cash, positions, pending_buys, pending_sells]`.
Each dictionary maps stock to quantity. Pending quantities are unfilled shares;
holdings and cash are totals, with no reservations deducted. Returned
dictionaries are independent snapshots; editing them does not change state.

The module stores only:

```python
users = {}  # user -> {"cash": int, "positions": {stock: quantity}}
books = {}  # stock -> {"buy": [...], "sell": [...]}
```

Book entries are `[user, remaining_quantity, limit_price]`. Pending portfolio
dictionaries are derived from the books. `reset()` clears all state for tests
or a new simulation; it is a Python helper, not a stdin command.

## Repeatable tests

These examples are executable tests. Run from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m doctest -v README.md
```

IPO creation, a non-crossing buy, a fill at the resting buy price, no reservations,
withdrawals, and independent snapshots:

```pycon
>>> import stock_exchange as ex
>>> ex.reset()
>>> ex.create_stock("issuer", "IBM", 10, 10)
>>> ex.add_user("alice")
>>> ex.deposit("alice", 100)
>>> ex.order("alice", "buy", "IBM", 4, 9)
[]
>>> ex.get_portfolio("alice")
[100, {}, {'IBM': 4}, {}]
>>> ex.get_portfolio("issuer")
[0, {'IBM': 10}, {}, {'IBM': 10}]
>>> ex.add_user("bob")
>>> ex.deposit("bob", 100)
>>> ex.order("bob", "buy", "IBM", 10, 12)
[['bob', 'issuer', 10, 10]]
>>> ex.order("bob", "sell", "IBM", 6, 8)
[['alice', 'bob', 4, 9]]
>>> ex.get_portfolio("bob")
[36, {'IBM': 6}, {}, {'IBM': 2}]
>>> ex.get_portfolio("alice")
[64, {'IBM': 4}, {}, {}]
>>> ex.withdraw("alice", 4)
>>> snapshot = ex.get_portfolio("alice")
>>> snapshot[1]["IBM"] = 999
>>> ex.get_portfolio("alice")
[60, {'IBM': 4}, {}, {}]
>>> ex.get_portfolio("issuer")
[100, {}, {}, {}]

```

Sell price priority, FIFO at equal prices, multiple fills, and a resting remainder:

```pycon
>>> ex.reset()
>>> ex.create_stock("issuer", "X", 30, 5)
>>> for name in ("a", "b", "c", "buyer"):
...     ex.add_user(name)
...     ex.deposit(name, 1000)
>>> for name in ("a", "b", "c"):
...     _ = ex.order(name, "buy", "X", 10, 5)
>>> ex.order("a", "sell", "X", 3, 9)
[]
>>> ex.order("b", "sell", "X", 3, 8)
[]
>>> ex.order("c", "sell", "X", 3, 8)
[]
>>> ex.order("buyer", "buy", "X", 10, 9)
[['buyer', 'b', 3, 8], ['buyer', 'c', 3, 8], ['buyer', 'a', 3, 9]]
>>> ex.get_portfolio("buyer")
[925, {'X': 9}, {'X': 1}, {}]

```

Buy price priority and FIFO at equal prices:

```pycon
>>> ex.reset()
>>> ex.create_stock("issuer", "X", 10, 20)
>>> ex.add_user("seller")
>>> ex.deposit("seller", 200)
>>> ex.order("seller", "buy", "X", 10, 20)
[['seller', 'issuer', 10, 20]]
>>> for name, price in (("a", 8), ("b", 9), ("c", 9)):
...     ex.add_user(name)
...     ex.deposit(name, 100)
...     _ = ex.order(name, "buy", "X", 2, price)
>>> ex.order("seller", "sell", "X", 5, 8)
[['b', 'seller', 2, 9], ['c', 'seller', 2, 9], ['a', 'seller', 1, 8]]
>>> ex.get_portfolio("a")
[92, {'X': 1}, {'X': 1}, {}]

```

A non-crossing sell, pending orders across stocks, and conservation of cash
and shares (continuing the preceding scenario):

```pycon
>>> ex.order("seller", "sell", "X", 3, 9)
[]
>>> ex.get_portfolio("seller")
[44, {'X': 5}, {}, {'X': 3}]
>>> ex.create_stock("other_issuer", "Y", 20, 2)
>>> ex.order("a", "buy", "Y", 4, 1)
[]
>>> ex.get_portfolio("a")
[92, {'X': 1}, {'X': 1, 'Y': 4}, {}]
>>> sum(user["cash"] for user in ex.users.values())
500
>>> {stock: sum(user["positions"].get(stock, 0) for user in ex.users.values()) for stock in ex.books}
{'X': 10, 'Y': 20}

```

Actual stdin/stdout, including all commands, silence for unfilled orders,
and separate holdings and pending lines:

```pycon
>>> import subprocess, sys
>>> commands = "\n".join(["create_stock co X 10 10", "add_user a", "deposit a 200", "withdraw a 20", "order a buy X 2 10", "order a buy X 3 9", "get_portfolio a", "get_portfolio co", ""])
>>> result = subprocess.run([sys.executable, "-B", "main.py"], input=commands, text=True, capture_output=True, check=True)
>>> result.stdout == "a co X 2 10\nCASH 160\nX 2\nX 3 PENDING_BUY\nCASH 20\nX 8\nX 8 PENDING_SELL\n"
True
>>> result.stderr
''
>>> ex.reset()
>>> (ex.users, ex.books)
({}, {})

```
