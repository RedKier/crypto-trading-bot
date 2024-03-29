import datetime

import tkinter as tk

from interface.styling import *
from interface.scrollable_frame import ScrollableFrame
from models import *


class TradesWatch(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._headers = ["time", "symbol", "exchange", "strategy", "side", "quntity", "status", "pnl"]

        self._table_frame = tk.Frame(self, bg=BG_COLOR)
        self._table_frame.pack(side=tk.TOP)

        self._headers_frame = tk.Frame(self._table_frame, bg=BG_COLOR)

        self._col_width = 11

        self.body_widgets = dict()

        for idx, h in enumerate(self._headers):
            header = tk.Label(self._headers_frame, text=h.capitalize(), bg=BG_COLOR,
                              fg=FG_COLOR, font=GLOBAL_FONT, width=self._col_width)
            header.grid(row=0, column=idx)

        header = tk.Label(self._headers_frame, text="", bg=BG_COLOR,
                          fg=FG_COLOR, font=GLOBAL_FONT, width=6)
        header.grid(row=0, column=len(self._headers))

        self._headers_frame.pack(side=tk.TOP, anchor="nw")

        self._body_frame = ScrollableFrame(self, bg=BG_COLOR, height=250)
        self._body_frame.pack(side=tk.TOP, anchor="nw", fill=tk.X)

        for h in self._headers:
            self.body_widgets[h] = dict()
            if h in ["status", "pnl"]:
                self.body_widgets[h + "_var"] = dict()

        self._body_index = 0

    def add_trade(self, data: Trade):
        b_index = self._body_index

        t_index = data.time

        dt_str = datetime.datetime.fromtimestamp(data.time / 1000).strftime("%b %d %H:%M")

        self.body_widgets['time'][t_index] = tk.Label(self._body_frame.sub_frame, text=dt_str, bg=BG_COLOR,
                                                      fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['time'][t_index].grid(row=b_index, column=0)

        self.body_widgets['symbol'][t_index] = tk.Label(self._body_frame.sub_frame, text=data.contract.symbol,
                                                        bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                        width=self._col_width)
        self.body_widgets['symbol'][t_index].grid(row=b_index, column=1)

        self.body_widgets['exchange'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                          text=data.contract.exchange.capitalize(),
                                                          bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                          width=self._col_width)
        self.body_widgets['exchange'][t_index].grid(row=b_index, column=2)

        self.body_widgets['strategy'][t_index] = tk.Label(self._body_frame.sub_frame, text=data.strategy, bg=BG_COLOR,
                                                          fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['strategy'][t_index].grid(row=b_index, column=3)

        self.body_widgets['side'][t_index] = tk.Label(self._body_frame.sub_frame, text=data.side.capitalize(),
                                                      bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                      width=self._col_width)
        self.body_widgets['side'][t_index].grid(row=b_index, column=4)

        self.body_widgets['quntity'][t_index] = tk.Label(self._body_frame.sub_frame, text=data.quantity, bg=BG_COLOR,
                                                         fg=FG_COLOR_2, font=GLOBAL_FONT, width=self._col_width)
        self.body_widgets['quntity'][t_index].grid(row=b_index, column=5)

        self.body_widgets['status_var'][t_index] = tk.StringVar()
        self.body_widgets['status'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                        textvariable=self.body_widgets['status_var'][t_index],
                                                        bg=BG_COLOR, fg=FG_COLOR_2, font=GLOBAL_FONT,
                                                        width=self._col_width)
        self.body_widgets['status'][t_index].grid(row=b_index, column=6)

        self.body_widgets['pnl_var'][t_index] = tk.StringVar()
        self.body_widgets['pnl'][t_index] = tk.Label(self._body_frame.sub_frame,
                                                     textvariable=self.body_widgets['pnl_var'][t_index], bg=BG_COLOR,
                                                     fg=FG_COLOR_2, font=GLOBAL_FONT)
        self.body_widgets['pnl'][t_index].grid(row=b_index, column=7)

        self._body_index += 1
