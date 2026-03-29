from collections import Counter
class ByteBPEv1:
    def __init__(self, corpus):
        """
        Initializes the ByteBPEv1 tokenizer.

        Args:
            corpus (str): The text corpus used to train the tokenizer.
        """
        self.vocab = [x for x in range(256)]
        self.corpus = list(corpus.encode("utf-8")) #text.encode(utf-8) gives us the byte stream, converting it into a list gives us the decimal representation
        self.decode_vocab = {x: bytes([x]) for x in range(256)} # mappiing of token (int) to byte sequence; bytes gives an immutable sequence of bytes (byte stream)
        self.merges = {}
        self.vocab_threshold = 1500
    
    # training phase starts here
    def split_corpus(self, max_byte_one, max_byte_two, merged_byte):
        """
        Updates the corpus by replacing all occurrences of the most frequent pair 
        (max_byte_one, max_byte_two) with the new merged_byte.

        Args:
            max_byte_one (int): The first byte/token of the pair to merge.
            max_byte_two (int): The second byte/token of the pair to merge.
            merged_byte (int): The new token ID representing the merged pair.
        """
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
        """
        Iterates through the current corpus to collect all adjacent token pairs.

        Returns:
            list: A list of tuples, where each tuple contains two adjacent tokens.
        """
        pairs = []
        for idx in range(len(self.corpus) - 1):
            byte_one = self.corpus[idx]
            byte_two = self.corpus[idx + 1]

            pairs.append((byte_one, byte_two))

        return pairs

    def build_vocab(self):
        """
        Trains the tokenizer by iteratively merging the most frequent token pairs
        until the vocabulary size reaches the threshold.
        """
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

    # training ends here

    def apply_merges(self,split_text):
        """
        Applies the learned merge rules to a sequence of tokens.

        Args:
            split_text (list): A list of initial tokens (bytes) representing the text.

        Returns:
            list: The list of tokens after applying all learned merges.
        """
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
        """
        Encodes a given text string into a list of BPE tokens.

        Args:
            text (str): The input text to encode.

        Returns:
            list: A list of integer tokens representing the encoded text.
        """
        split_text = list(text.encode("utf-8"))
        token_list = self.apply_merges(split_text) # returns a list
        return token_list


    def decode(self, token_list):
        """
        Decodes a list of BPE tokens back into a string.

        Args:
            token_list (list): A list of integer tokens to decode.

        Returns:
            str: The decoded text string.
        """
        byte_lst = []

        for token in token_list:
            byte_lst.append(self.decode_vocab[token])


        byte_lst_joined = b''.join(byte_lst)
        return byte_lst_joined.decode("utf-8")
    

if __name__ == "__main__":
    # Define a training corpus with repeated patterns
    corpus = """
    The quick brown fox jumps over the lazy dog. The quick brown fox is very quick.
    Machine learning is fascinating. Machine learning models learn from data.
    Python is a great programming language. Python makes coding easier.
    The cat sat on the mat. The cat likes the warm mat.
    Hello world! Hello everyone in the world!
    """
    
    print("=" * 60)
    print("TRAINING BPE TOKENIZER")
    print("=" * 60)
    print(f"\nTraining corpus length: {len(corpus)} characters")
    print(f"Training corpus bytes: {len(corpus.encode('utf-8'))} bytes\n")
    
    # Initialize and train the tokenizer
    tokenizer = ByteBPEv1(corpus)
    print("Building vocabulary...")
    tokenizer.build_vocab()
    print("Training complete!\n")
    
    # Print vocabulary information
    print("=" * 60)
    print("VOCABULARY INFORMATION")
    print("=" * 60)
    print(f"Final vocab size: {len(tokenizer.vocab)}")
    print(f"Number of merges learned: {len(tokenizer.merges)}")
    print(f"\nFirst 20 learned merges:")
    print("-" * 60)
    
    for i, ((byte1, byte2), merged) in enumerate(list(tokenizer.merges.items())[:20]):
        # Try to decode the bytes for display
        try:
            char1 = tokenizer.decode_vocab[byte1].decode('utf-8', errors='replace')
            char2 = tokenizer.decode_vocab[byte2].decode('utf-8', errors='replace')
            merged_str = tokenizer.decode_vocab[merged].decode('utf-8', errors='replace')
            print(f"{i+1}. ({byte1}, {byte2}) -> {merged} | '{char1}' + '{char2}' = '{merged_str}'")
        except:
            print(f"{i+1}. ({byte1}, {byte2}) -> {merged}")
    
    # Test encode/decode methods
    print("\n" + "=" * 60)
    print("ENCODE/DECODE TESTS")
    print("=" * 60)
    
    test_strings = [
        "The quick brown fox",
        "Machine learning",
        "Hello world!",
        "Python programming",
        "This is a new sentence not in the corpus"
    ]
    
    for i, test_text in enumerate(test_strings, 1):
        print(f"\nTest {i}:")
        print("-" * 60)
        print(f"Original text: '{test_text}'")
        
        # Encode
        encoded = tokenizer.encode(test_text)
        print(f"Encoded tokens: {encoded}")
        print(f"Number of tokens: {len(encoded)}")
        
        # Decode
        decoded = tokenizer.decode(encoded)
        print(f"Decoded text: '{decoded}'")
        
        # Compression ratio
        original_bytes = len(test_text.encode('utf-8'))
        num_tokens = len(encoded)
        compression_ratio = original_bytes / num_tokens if num_tokens > 0 else 0
        print(f"Original bytes: {original_bytes}, Tokens: {num_tokens}")
        print(f"Compression ratio: {compression_ratio:.2f}x")
        print(f"Match: {decoded == test_text}")
    
    print("\n" + "=" * 60)
    print("TESTING COMPLETE")
    print("=" * 60)