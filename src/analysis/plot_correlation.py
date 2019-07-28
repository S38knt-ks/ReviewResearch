import pandas
import numpy as np
import matplotlib.pyplot as plt

def calc_correlation_coefficient(x, y):
    """
    ピアソンの相関係数の計算
    """
    x_series = pandas.Series(x)
    y_series = pandas.Series(y)
    return x_series.corr(y_series)


def convert_nan_to_num(nan_x, dtype=np.float32, normalize=False):
    """
    Not a Number(数じゃないもの)を無理やり数字化して、プロットできるようにする
    """
    nan_x_arr  = np.array(nan_x)
    nan_to_num = {_x: idx for idx, _x in enumerate(np.unique(nan_x_arr))}
    x = np.zeros(nan_x_arr.shape, dtype=dtype)
    for nan in nan_to_num:
        x[nan_x == nan] = nan_to_num[nan]

    return x

class CorrPlotter:
    """
    2変数の相関関係のプロットをおこなう
    """

    DEFAULT_FIGSIZE = (16, 9)
    ALT_XTICKS_ROT_DEGREE = 90

    def __init__(self, figsize=None):
        self._figsize = self.DEFAULT_FIGSIZE


    def plot(self, x, y, x_label, y_label, figname, alt_xticks=None):
        plt.figure(figsize=self._figsize)
        plt.scatter(x, y)

        if alt_xticks:
            plt.xticks(x, alt_xticks, rotation=self.ALT_XTICKS_ROT_DEGREE)

        plt.xlabel(x_label)
        plt.ylabel(y_label)

        R = calc_correlation_coefficient(x, y)
        plt.title('R = {}'.format(R))
        plt.tight_layout()
        plt.savefig(figname)
        plt.clf()
        plt.close()


