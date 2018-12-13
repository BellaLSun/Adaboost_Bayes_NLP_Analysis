'''
多类的朴素贝叶斯实现
'''
import random
import re
import traceback

import jieba
import matplotlib.pyplot as plt
import numpy as np
from pylab import mpl
from sklearn.externals import joblib
from sklearn.naive_bayes import MultinomialNB

jieba.load_userdict("../train/word.txt")
stop = [line.strip() for line in open('../ad/stop.txt', 'r', encoding='utf-8').readlines()]  # 停用词


def build_key_word(path):  # 通过词频产生特征
    d = {}
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            for word in jieba.cut(line.strip()):
                # \b表示单词边界,开始的(\w+)表示一个单词
                p = re.compile(b'\w', re.L)
                result = p.sub(b"", bytes(word, encoding="utf-8")).decode("utf-8")
                if not result or result == ' ':  # 空字符
                    continue
                if len(word) > 1:  # 避免大量无意义的词语进入统计范围
					# dict.get(key, default=None)
                    d[word] = d.get(word, 0) + 1
    kw_list = sorted(d, key=lambda x: d[x], reverse=True) # len = 2191
    size = int(len(kw_list) * 0.2)  # 取最前的20%
	# 集合（set）是一个无序的不重复元素序列。
    mood = set(kw_list[:size]) # 438
    return list(mood - set(stop))


def loadDataSet(path):  # 返回每条微博的分词与标签
    line_cut = []
    label = []
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            temp = line.strip() # 去掉/n
            try:
                sentence = temp[2:].lstrip()  # 每条微博 # 返回截掉字符串左边的空格或指定字符
                label.append(int(temp[:2]))  # 获取标注
                word_list = []
                sentence = str(sentence).replace('\u200b', '') # '\u200b', ZERO WIDTH SPACE
                for word in jieba.cut(sentence.strip()):
                    p = re.compile(b'\w', re.L)
                    result = p.sub(b"", bytes(word, encoding="utf-8")).decode("utf-8")
                    if not result or result == ' ':  # 空字符
                        continue
                    word_list.append(word)
                word_list = list(set(word_list) - set(stop) - set('\u200b')
                                 - set(' ') - set('\u3000') - set('️'))   #\u3000全角空格(中文符号)
                line_cut.append(word_list)
            except Exception:
                continue
    return line_cut, label  # 返回每条微博的分词和标注


# vocabList = build_key_word("../train/train.txt")
def setOfWordsToVecTor(vocabularyList, moodWords):  # 每条微博向量化
    vocabMarked = [0] * len(vocabularyList) #len=307
    for smsWord in moodWords:
        if smsWord in vocabularyList:
			# 原来是0，找到地方，把原来是0的index变成1
            vocabMarked[vocabularyList.index(smsWord)] += 1
    return np.array(vocabMarked)


def setOfWordsListToVecTor(vocabularyList, train_mood_array):  # 将所有微博准备向量化 # train_mood_array:每条微博切词后的list集合
    vocabMarkedList = []
    for i in range(len(train_mood_array)): # 510
		# 得到每条微博的词向量
        vocabMarked = setOfWordsToVecTor(vocabularyList, train_mood_array[i])
        # 所有微博的list集合
        vocabMarkedList.append(vocabMarked)
    return vocabMarkedList


def trainingNaiveBayes(train_mood_array, label):  # train_mood_array：计算先验概率 # 410个文本，每个文本中有307个词向量
    numTrainDoc = len(train_mood_array) # 410
    numWords = len(train_mood_array[0]) #307
    prior_Pos, prior_Neg, prior_Neutral = 0.0, 0.0, 0.0
    for i in label:
        if i == 1:
            prior_Pos = prior_Pos + 1
        elif i == 2:
            prior_Neg = prior_Neg + 1
        else:
            prior_Neutral = prior_Neutral + 1
    prior_Pos = prior_Pos / float(numTrainDoc) # 积极数量在train中所有微博数的比率
    prior_Neg = prior_Neg / float(numTrainDoc)
    prior_Neutral = prior_Neutral / float(numTrainDoc)
	# 构造积极/消极/中立 词向量
    wordsInPosNum = np.ones(numWords)
    wordsInNegNum = np.ones(numWords)
    wordsInNeutralNum = np.ones(numWords)
    PosWordsNum = 2.0  # 如果一个概率为0，乘积为0，故初始化1，分母2
    NegWordsNum = 2.0
    NeutralWordsNum = 2.0
    for i in range(0, numTrainDoc):
        try:
            if label[i] == 1:
				# train_mood_array：410*307
                wordsInPosNum += train_mood_array[i] # wordsInPosNum：307，
                PosWordsNum += sum(train_mood_array[i])  # 统计Pos的词在语料库中词汇出现的总次数
            elif label[i] == 2:
                wordsInNegNum += train_mood_array[i]
                NegWordsNum += sum(train_mood_array[i])
            else:
                wordsInNeutralNum += train_mood_array[i]
                NeutralWordsNum += sum(train_mood_array[i])
        except Exception as e:
            traceback.print_exc(e)
	# 归一化-》log
    pWordsPosicity = np.log(wordsInPosNum / PosWordsNum)
    pWordsNegy = np.log(wordsInNegNum / NegWordsNum)
    pWordsNeutral = np.log(wordsInNeutralNum / NeutralWordsNum)
    # 返回词向量&比率
    return pWordsPosicity, pWordsNegy, pWordsNeutral, prior_Pos, prior_Neg, prior_Neutral

#
def classify(pWordsPosicity, pWordsNegy, pWordsNeutral, prior_Pos, prior_Neg, prior_Neutral,
             test_word_arrayMarkedArray): # test_word_array
	# 先验分布 π(θ)+ 样本信息χ⇒  后验分布π(θ|x)
	# 后验分布π(θ|x)一般也认为是在给定样本χ的情况下θ的条件分布，而使达到最大的值称为最大后θMD验估计，类似于经典统计学中的极大似然估计。
    # pWordsPosicity和np.log(prior_Pos)都是样本得到的先验数据指标
    pP = sum(test_word_arrayMarkedArray * pWordsPosicity) + np.log(prior_Pos)
    pN = sum(test_word_arrayMarkedArray * pWordsNegy) + np.log(prior_Neg)
    pNeu = sum(test_word_arrayMarkedArray * pWordsNeutral) + np.log(prior_Neutral)

    if pP > pN > pNeu or pP > pNeu > pN:
        return pP, pN, pNeu, 1
    elif pN > pP > pNeu or pN > pNeu > pP:
        return pP, pN, pNeu, 2
    else:
        return pP, pN, pNeu, 3

# 预测的错误率
def predict(test_word_array, test_word_arrayLabel, testCount, PosWords, NegWords, NeutralWords, prior_Pos, prior_Neg,
            prior_Neutral):
    errorCount = 0
    for j in range(testCount):
        try:
            pP, pN, pNeu, smsType = classify(PosWords, NegWords, NeutralWords, prior_Pos, prior_Neg, prior_Neutral,
                                             test_word_array[j])
            if smsType != test_word_arrayLabel[j]:
                errorCount += 1
        except Exception as e:
            traceback.print_exc(e)
    print("Bayes", errorCount / testCount)
    return errorCount / testCount


if __name__ == '__main__':
    multi_nb = []
    bayes_nb = []
    for m in range(1, 51):
        vocabList = build_key_word("../train/train.txt")
        line_cut, label = loadDataSet("../train/train.txt")
        train_mood_array = setOfWordsListToVecTor(vocabList, line_cut)
        test_word_array = []
        test_word_arrayLabel = []
        testCount = 100  # 从中随机选取100条用来测试，并删除原来的位置
        for i in range(testCount):
            try:
                randomIndex = int(random.uniform(0, len(train_mood_array)))
                test_word_arrayLabel.append(label[randomIndex])
                test_word_array.append(train_mood_array[randomIndex])
                del (train_mood_array[randomIndex])
                del (label[randomIndex])
            except Exception as e:
                print(e)

		# 调包
        multi = MultinomialNB()
        multi = multi.fit(train_mood_array, label)
        joblib.dump(multi, '../model/gnb.model')
        muljob = joblib.load('../model/gnb.model')
        result = muljob.predict(test_word_array)
        count = 0
        for i in range(len(test_word_array)):
            type = result[i]
            if type != test_word_arrayLabel[i]:
                count = count + 1
                # print(test_word_array[i], "----", result[i])
        print("MultinomialNB", count / float(testCount))
        multi_nb.append(count / float(testCount))
		# 自己写的
        PosWords, NegWords, NeutralWords, prior_Pos, prior_Neg, prior_Neutral = \
            trainingNaiveBayes(train_mood_array, label)
        accuracy = predict(test_word_array, test_word_arrayLabel, testCount, PosWords, NegWords, NeutralWords,
                           prior_Pos, prior_Neg,
                           prior_Neutral)
        bayes_nb.append(accuracy)

    # 画图
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([x for x in range(1, 51)], multi_nb,
            label='sklearn',
            color='orange')
    ax.plot([x for x in range(1, 51)], bayes_nb,
            label='hand-written Realisation',
            color='green')
    ax.set_xlabel('Iterations')
    ax.set_ylabel('Accuracy')
    plt.xlim([1,50])
    leg = ax.legend(loc='upper right', fancybox=True)
    leg.get_frame().set_alpha(0.7)
    plt.title("Comparision")
    plt.show()
