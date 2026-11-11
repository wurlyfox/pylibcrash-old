typedef struct trie_node {
  int value;
  int idx;
  struct trie_node *parent;
  struct trie_node *child;
  struct trie_node *next;
} trie_node;
typedef struct {
  trie_node *root;
  trie_node nodes[0x1000000*4];
  trie_node *leaves[0x400];
  trie_node *free_nodes[0x1000000*4];
  int node_count;
  int leaf_count;
  int free_node_count;
} suffix_tree;
extern void suffix_tree_init(suffix_tree *tree);
extern trie_node *suffix_tree_insert(suffix_tree *tree, int, int);
extern void suffix_tree_delete(suffix_tree *tree, trie_node *node);
extern trie_node *suffix_tree_find_child(trie_node *node, int value);
