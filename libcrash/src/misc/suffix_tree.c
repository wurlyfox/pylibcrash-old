#include "misc/suffix_tree.h"

static inline trie_node *suffix_tree_node_alloc(suffix_tree *tree) {
  int idx;
  trie_node *node;
  
  idx = SUFFIX_TREE_NODES_MAX - tree->free_node_count--;
  node = tree->free_nodes[idx];
  tree->node_count++;  
  return node;
}

static inline void suffix_tree_node_free(suffix_tree *tree, 
                                         trie_node *node) {
  int idx;
  
  idx = SUFFIX_TREE_NODES_MAX - ++tree->free_node_count;
  tree->free_nodes[idx] = node;
  tree->node_count--;
  return node;
}

void suffix_tree_init(suffix_tree *tree) {
  int i;
  trie_node *root;
  
  tree->node_count = 0;
  tree->free_node_count = sizeof(tree->free_nodes)/sizeof(trie_node*);
  for (i=0;i<tree->free_node_count;i++) {
    tree->free_nodes[i] = &tree->nodes[i];
  }
  
  root = suffix_tree_node_alloc(tree);
  memset(root, 0, sizeof(trie_node));
  root->idx = -1;
  
  tree->root = root;
  tree->leaves[0] = root;
  tree->leaf_count = 1;
}

#define min(a,b) ((a)<(b)?(a):(b))
trie_node *suffix_tree_insert(suffix_tree *tree, int value, int idx) {
  int i,ii,depth;
  trie_node *node, *parent, *prev;
    
  prev = 0;
  for (i=0;i<min(tree->leaf_count,SUFFIX_TREE_DEPTH_MAX);i++) {
    parent = tree->leaves[i];
    node = parent->child;
    while (node) {
      if (node->value == value) break;
      prev = node;
      node = node->next;
    }
    if (!node) {
      node = suffix_tree_node_alloc(tree);
      node->parent = parent;
      node->child = 0;
      node->next = 0;
      if (!parent->child)
        parent->child = node;
      else
        prev->next = node;
    }
    node->value = value;
    node->idx = idx;
    tree->leaves[i] = node;
  }
  
  idx = tree->leaf_count % SUFFIX_TREE_DEPTH_MAX;
  tree->leaves[idx] = tree->root;
  tree->leaf_count++;
  
  return node;
}

void suffix_tree_delete(suffix_tree *tree, trie_node *node) {
  int i;
  trie_node *parent, *prev;
  
  while (node->parent && (parent = node->parent) &&
         parent->idx == node->idx-1 && !parent->child->next) {
    suffix_tree_node_free(tree, node);
    parent->child = 0;
    node = parent;
  }
  if (parent->child == node)
    parent->child = parent->child->next;
  else {
    for (prev=parent->child;prev->next!=node;prev=prev->next);
    prev->next = node->next;
  }
  suffix_tree_node_free(tree, node);
}

trie_node *suffix_tree_find_child(trie_node *node, int value) {
  if (!node) return 0;
  for (node=node->child;node;node=node->next)
    if (node->value == value) break;
  return node;
}
