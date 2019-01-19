from unittest import TestCase

import numpy as np
import pandas as pd
from gensim.models import Word2Vec

import qiqc


class TestWordFeatures(TestCase):

    def test_build_feature(self):
        vocab = qiqc.features.WordVocab()
        vocab.add_documents([
            list('aa'),
            list('ab'),
            list('abc'),
            list('abcd'),
            list('abcde`'),
        ], 'test')
        vocab.build()
        min_count = 3
        unk = np.arange(len(vocab)) % 2 == 0
        lfq = np.array([i < min_count for i in vocab.word_freq.values()])
        embed_shape = (len(vocab), 300)
        pretrained_vectors = np.random.normal(0, 1, embed_shape)
        pretrained_vectors[unk] = 0
        feature = qiqc.features.WordFeature(
            vocab, pretrained_vectors, min_count)

        # Basic case
        vectors = feature.build_feature(add_noise=None)
        np.testing.assert_allclose(vectors, pretrained_vectors)

        # Test to add noise for high frequent word vectors
        vectors = feature.build_feature(add_noise='unk&hfq')
        is_equal = vectors == pretrained_vectors
        np.testing.assert_equal(vectors[lfq & unk], 0)
        np.testing.assert_equal(is_equal.all(axis=1), lfq | ~unk)

        # Test skipgram finetuning
        df = pd.DataFrame(
            {'tokens': [list('abcd'), list('abcdefg'), list('adefg')]})
        feature.finetune(Word2Vec, df)
        vectors = feature.build_feature(add_noise='unk&hfq')
        is_equal = vectors == pretrained_vectors
        np.testing.assert_equal(vectors[lfq & unk], 0)
        np.testing.assert_equal(is_equal.all(axis=1), lfq & unk)
