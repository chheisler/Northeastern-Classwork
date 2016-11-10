from random import randint
import numpy as np
from matplotlib import pyplot
from util import load_data, zscore, DATA_AXIS, FEATURE_AXIS

NUM_TRIALS = 25
MAX_ITERS = 50
INDICES = [773, 1010, 240, 126, 319, 1666, 1215, 551, 668, 528, 1060, 168, 402,
80, 115, 221, 242, 1951, 1725, 754, 1469, 135, 877, 1287, 645, 272, 1203, 1258,
1716, 1158, 586, 1112, 1214, 153, 23, 510, 05, 1254, 156, 936, 1184, 1656, 244,
811, 1937, 1318, 27, 185, 1424, 190, 663, 1208, 170, 1507, 1912, 1176, 1616,
109, 274, 1, 1371, 258, 1332, 541, 662, 1483, 66, 12, 410, 1179, 1281, 145,
1410, 664, 155, 166, 1900, 1134, 1462, 954, 1818, 1679, 832, 1627, 1760, 1330,
913, 234, 1635, 1078, 640, 833, 392, 1425, 610, 1353, 1772, 908, 1964, 1260,
784, 520, 1363, 544, 426, 1146, 987, 612, 1685, 1121, 1740, 287, 1383, 1923,
1665, 19, 1239, 251, 309, 245, 384, 1306, 786, 1814, 7, 1203, 1068, 1493, 859,
233, 1846, 1119, 469, 1869, 609, 385, 1182, 1949, 1622, 719, 643, 1692, 1389,
120, 1034, 805, 266, 339, 826, 530, 1173, 802, 1495, 504, 1241, 427, 1555,
1597, 692, 178, 774, 1623, 1641, 661, 1242, 1757, 553, 1377, 1419, 306, 1838,
211, 356, 541, 1455, 741, 583, 1464, 209, 1615, 475, 1903, 555, 1046, 379,
1938, 417, 1747, 342, 1148, 1697, 1785, 298, 185, 1145, 197, 1207, 1857, 158,
130, 1721, 1587, 1455, 190, 177, 1345, 166, 1377, 1958, 1727, 1134, 1953, 1602,
114, 37, 164, 1548, 199, 1112, 128, 167, 102, 87, 25, 249, 1240, 1524, 198,
111, 1337, 1220, 1513, 1727, 159, 121, 1130, 1954, 1561, 1260, 150, 1613, 1152,
140, 1473, 1734, 137, 1156, 108, 110, 1829, 1491, 1799, 174, 847, 177, 1468,
97, 1611, 1706, 1123, 79, 171, 130, 100, 143, 1641, 181, 135, 1280, 1442, 1188,
133, 99, 186, 1854, 27, 160, 130, 1495, 101, 1411, 814, 109, 95, 111, 1582,
1816, 170, 1663, 1737, 1710, 543, 1143, 1844, 159, 48, 375, 1315, 1311, 1422]

def cluster(data, k, trial):
    # initialize centroids
    centroids = np.zeros((k, data.shape[FEATURE_AXIS]))
    for i in range(k):
        centroids[i] = data[INDICES[k * trial + i] - 1].copy()

    # initialize some random clusters
    clusters = np.zeros(data.shape[DATA_AXIS])
    clusterer = lambda datum: _cluster(datum, centroids)

    # iterate until maximum iterations or until nothing changes
    for i in range(MAX_ITERS):
        new_clusters = np.apply_along_axis(clusterer, FEATURE_AXIS, data)
        done = (clusters != new_clusters).sum() == 0
        clusters = new_clusters
        for j, centroid in enumerate(centroids):
            indices = np.where(clusters == j)
            centroids[j] = data[indices].mean(DATA_AXIS)
        if done:
            break

    # return the results
    return (centroids, clusters)

def _cluster(datum, centroids):
    distances = np.sqrt(((centroids - datum) ** 2).sum(axis=FEATURE_AXIS))
    return distances.argsort()[0]

def main():
    # load the data
    data, labels = load_data(open('segment.arff','r'))
    data = zscore(data)

    # set up the plot to draw
    pyplot.figure()
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    y = []

    # run the trials
    for k in x:
        #print
        sse = np.zeros(NUM_TRIALS)        
        for i in range(NUM_TRIALS):
            centroids, clusters = cluster(data, k, i)
            for j, centroid in enumerate(centroids):
                indices = np.where(clusters == j)
                total = 0.0
                sse[i] += ((data[indices] - centroid) ** 2).sum()
            #print "k=%d,trial=%d,SSE=%f" % (k, i, sse[i])
        mean = sse.mean()
        std = sse.std(ddof=1)
        #print "k=%d,mean=%f,std-=%f,std+" % (k, mean, std)
        print "%d & %f & %f & %f \\" % (k,mean,mean-2*std,mean+2*std)
        y.append(mean)
        pyplot.errorbar(k, mean, yerr=2*std, color="red")

    # draw the final graph
    pyplot.title("SSE for K-Means")
    pyplot.xlim(1,12)
    pyplot.xlabel("k")
    pyplot.ylabel("SSE")
    pyplot.plot(x, y, color="blue")
    pyplot.savefig('kmeans.png')

if __name__ == '__main__':
    main()
