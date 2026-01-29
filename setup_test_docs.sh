#!/bin/bash
# Create test documents for batch processing

mkdir -p test_documents

cat > test_documents/doc1.txt << 'EOF'
Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on the development of algorithms and statistical models that enable computer systems to improve their performance on a specific task through experience.

The field has grown exponentially in recent years, with applications ranging from natural language processing to computer vision, and from recommendation systems to autonomous vehicles.
EOF

cat > test_documents/doc2.txt << 'EOF'
Deep Learning Fundamentals

Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers to progressively extract higher-level features from raw input.

The key innovation of deep learning is the ability to automatically learn hierarchical representations of data, which has led to breakthrough performances in image recognition, speech recognition, and natural language understanding.
EOF

cat > test_documents/doc3.txt << 'EOF'
Natural Language Processing

Natural Language Processing (NLP) is a branch of artificial intelligence that helps computers understand, interpret and manipulate human language.

Modern NLP applications include machine translation, sentiment analysis, question answering systems, and chatbots. Recent advances in transformer architectures have revolutionized the field.
EOF

cat > test_documents/doc4.txt << 'EOF'
Computer Vision

Computer vision is an interdisciplinary field that deals with how computers can gain high-level understanding from digital images or videos.

Applications include object detection, facial recognition, image segmentation, and autonomous navigation. Convolutional neural networks have become the standard architecture for most computer vision tasks.
EOF

cat > test_documents/doc5.txt << 'EOF'
Reinforcement Learning

Reinforcement learning is an area of machine learning concerned with how intelligent agents ought to take actions in an environment to maximize cumulative reward.

Key concepts include the agent, environment, state, action, and reward. Applications range from game playing to robotics to resource management.
EOF

echo "Created 5 test documents in test_documents/"
ls -lh test_documents/
echo ""
echo "Sample content from doc1.txt:"
head -5 test_documents/doc1.txt
