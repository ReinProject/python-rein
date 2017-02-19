import scrypt
import time
from bitcoin.core import x, b2x

if __name__ == '__main__':
    text = """-----BEGIN BITCOIN SIGNED MESSAGE-----
- ----BEGIN BITCOIN SIGNED MESSAGE-----
- ----BEGIN BITCOIN SIGNED MESSAGE-----
Name/Handle: Knightdk
Contact: knightdk on Bitcointalk.org
Master signing address: 16mT7jrpkjnJBD7a3TM2awyxHub58H6r6Z
Delegate signing address: N/A
Willing to mediate: Y
Mediation public key: 04594f2582c859c4f65084ee7fe8e9ec2d695bb988a3f53db48eaaff6ff3a0282b2be0c79"""\
"""fefca01277404d0fdc3a923e8ed02efd6ab96980f3e229a81fbe032e9
- ----BEGIN SIGNATURE-----
16mT7jrpkjnJBD7a3TM2awyxHub58H6r6Z
GxHE6iJH2aMpsRk7cszvXsLieDawzArpt7XDdOPhVFD5KVqIvKve1fwUKeN6ct4bld41XLdrZ7Dvaj7x1Oiw0uo=
- ----END BITCOIN SIGNED MESSAGE-----
- ----BEGIN SIGNATURE-----
1BbgnPQYeXAt39ifLNUWP1RBktpzGLmRZS
IGJcg+MoqpBQNtptelyZfC2zBKk5SZQQjtf4pHSxb0yZH6kn/9Dhd1TWFfXUXsWmZq78xYye4lKi1aQUeNQ2ZFs=
- ----END BITCOIN SIGNED MESSAGE-----
-----BEGIN SIGNATURE-----
1DVK9Rdi2wcpcfEkep7FSNUui7fzadmxsW
IMcU7MvLl7T+hY0mmMw6mblLstnXd9Ly36z7uYMqv7ZZEuZQOvuXN2GjYU0Nq4So9GKQRkQwIis7EiN6luTMcOY=
-----END BITCOIN SIGNED MESSAGE-----"""

    start = time.time()
    count = 1
    
    h1 = scrypt.hash(text, 'random salt', 32768, 8, 1, 16)
    while 1:
        h1 = scrypt.hash(h1, 'random salt', 32768, 8, 1, 16)
        count += 1
        if h1 < x('04ffffffffffffffffffffffffffffff'):
            print(b2x(h1), time.time() - start, count)
