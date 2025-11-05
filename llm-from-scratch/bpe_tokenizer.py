from collections import Counter
class byteBPE:
    def __init__(self, corpus):
        self.vocab = [x for x in range(256)]
        self.corpus = list(corpus.encode("utf-8")) #text.encode(utf-8) gives us the byte stream, converting it into a list gives us the decimal representation
        self.decode_vocab = {x: bytes([x]) for x in range(256)} # bytes gives an immutable sequence of bytes (byte stream)
        self.merges = {}
        self.vocab_threshold = 1500
    
    def split_corpus(self, max_byte_one, max_byte_two, merged_byte):
        skip_indices = set()
        for idx in range(len(self.corpus) - 1):
            byte_one = self.corpus[idx]
            byte_two = self.corpus[idx + 1]

            if byte_one == max_byte_one and byte_two == max_byte_two:
                skip_indices.add(idx)
                self.corpus[idx + 1] = merged_byte
        
        new_corpus = []
        for idx in range(len(self.corpus)):
            if idx in skip_indices:
                continue
            else:
                new_corpus.append(self.corpus[idx])
        self.corpus = new_corpus

    
    def build_pairs(self):
        pairs = []
        for idx in range(len(self.corpus) - 1):
            byte_one = self.corpus[idx]
            byte_two = self.corpus[idx + 1]

            pairs.append((byte_one, byte_two))

        return pairs

    def build_vocab(self):
        while len(self.vocab) < self.vocab_threshold:
            pairs = self.build_pairs()
            frequency_counter = Counter(pairs)

            if not frequency_counter:
                break
    
            max_byte_one, max_byte_two = max(frequency_counter.items(), key = lambda x:x[1])[0]
            merged_byte = len(self.vocab)
            self.merges[(max_byte_one, max_byte_two)] = merged_byte

            self.vocab.append(merged_byte)
            bytes_one = self.decode_vocab[max_byte_one]
            bytes_two = self.decode_vocab[max_byte_two]
            self.decode_vocab[merged_byte] = bytes_one + bytes_two


            self.split_corpus(max_byte_one, max_byte_two, merged_byte)


    def encode(self):
        pass

    def decode(self):
        pass
    

