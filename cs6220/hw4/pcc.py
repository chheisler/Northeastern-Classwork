from math import sqrt

def pcc(x, y):
    n = len(x)
    sum_sq_x = 0
    sum_sq_y = 0
    sum_coproduct = 0
    mean_x = 0
    mean_y = 0
    for i in range(n):
        sum_sq_x += x[i] ** 2
        sum_sq_y += y[i] ** 2
        sum_coproduct += x[i] * y[i]
        mean_x += x[i]
        mean_y += y[i]
    mean_x /= n
    mean_y /= n
    std_x = sqrt(sum_sq_x / n - mean_x ** 2)
    std_y = sqrt(sum_sq_y / n - mean_y ** 2)
    covar = sum_coproduct / n - mean_x * mean_y
    correlation = covar / (std_x * std_y)
    return correlation
