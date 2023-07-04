#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jaakko Ahola
@company:  Virnex Oy
@date: 
"""

import os
import sys
import time
from datetime import datetime

sys.path.append(os.environ["LESMAINSCRIPTS"])
from Data import Data


def main():
    pass


if __name__ == "__main__":
    start = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script started {now}.")
    main()
    end = time.time()
    now = datetime.now().strftime('%d.%m.%Y %H.%M')
    print(f"Script completed {now} in {Data.timeDuration(end - start)}")
