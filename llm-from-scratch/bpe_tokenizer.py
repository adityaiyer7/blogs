from collections import Counter
class ByteBPE:
    def __init__(self, corpus):
        self.vocab = [x for x in range(256)]
        self.corpus = list(corpus.encode("utf-8")) #text.encode(utf-8) gives us the byte stream, converting it into a list gives us the decimal representation
        self.decode_vocab = {x: bytes([x]) for x in range(256)} # bytes gives an immutable sequence of bytes (byte stream)
        self.merges = {}
        self.vocab_threshold = 1500
    
    # training phase starts here
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

    # training ends starts here

    def apply_merges(self,split_text):
        for (max_byte_one, max_byte_two), merged_byte in self.merges.items():
            skip_indices = set()
            for idx in range(len(split_text) - 1):
                byte_one = split_text[idx]
                byte_two = split_text[idx + 1]

                if byte_one == max_byte_one and byte_two == max_byte_two:
                    skip_indices.add(idx)
                    split_text[idx + 1] = merged_byte
            
            new_text = []
            for idx in range(len(split_text)):
                if idx in skip_indices:
                    continue
                else:
                    new_text.append(split_text[idx])
            split_text = new_text
        return split_text

    def encode(self, text):
        split_text = list(text.encode("utf-8"))
        token_list = self.apply_merges(split_text) # returns a list
        return token_list


    def decode(self, token_list):
        byte_lst = []

        for token in token_list:
            byte_lst.append(self.decode_vocab[token])


        byte_lst_joined = b''.join(byte_lst)
        return byte_lst_joined.decode("utf-8")
    

