

# **Architectural Paradigms in Neural Code Intelligence: A Comprehensive Empirical Analysis of Explanation-First Prompting Strategies for Software Reliability**

## **1\. Introduction: The Interpretability Crisis in Neural Software Engineering**

The rapid assimilation of Large Language Models (LLMs) into the software engineering (SE) lifecycle has precipitated a fundamental transformation in how code is synthesized, analyzed, and debugged. We have moved from an era of heuristic-based static analysis and template-driven generation to one dominated by stochastic, generative intelligence. However, this shift has introduced a critical "black box" problem: while LLMs demonstrate emergent capabilities in vulnerability detection and code generation, their decision-making processes remain opaque, creating a barrier to trust in high-stakes environments such as cybersecurity and critical infrastructure development.  
The central tension in current research lies between performance and interpretability. Early implementations favored direct prediction—mapping a code snippet to a vulnerability label or a natural language description to executable code. While computationally efficient, this approach lacks transparency. When an LLM flags a function as "vulnerable," is it reacting to a genuine data flow anomaly, or is it identifying a spurious correlation, such as a variable name common in training data exploits? The literature suggests that without explicit reasoning mechanisms, models frequently engage in "shortcut learning," leading to high false-positive rates and hallucinated bugs.  
To mitigate this, the field is converging on **Explanation Prompting** as a mechanism to align model outputs with logical reasoning. This report provides an exhaustive analysis of the two dominant architectural paradigms: **Predict-Then-Explain (PE)** and **Explain-Then-Predict (EP)**. Specifically, we validate the hypothesis that "explain-before" designs—exemplified by Chain-of-Thought (CoT), Structured Chain-of-Thought (SCoT), and the R2Vul framework—offer superior faithfulness and utility compared to post-hoc rationalization. By forcing the model to externalize its reasoning trace prior to committing to a prediction, we theoretically constrain the generative process to valid logical paths, thereby enhancing both the correctness of the code and the reliability of the vulnerability assessment.  
The following analysis synthesizes empirical evidence from recent studies (2023-2025) to guide the design of a robust validation study for explain-before prompting. We explore the theoretical underpinnings of rationalization versus reasoning, the architectural innovations in structured prompting, and the rigorous evaluation rubrics required to measure the elusive quality of "faithfulness."  
---

## **2\. Theoretical Framework: The Temporal Dynamics of Reasoning**

The distinction between explaining before prediction and explaining after prediction is not merely a matter of prompt engineering syntax; it represents a fundamental difference in the cognitive architecture simulated by the model. Understanding this dichotomy is essential for evaluating the validity of generated explanations.

### **2.1 The Predict-Then-Explain (PE) Paradigm: Post-Hoc Rationalization**

The Predict-Then-Explain (PE) paradigm, sometimes referred to as "rationalization," operates on the premise that the model's primary task is decision-making, with explanation serving as a secondary, justifications layer.1 In this workflow, the model first outputs a label (e.g., Vulnerable) or a code solution, and subsequently generates a natural language text explaining *why* that output was produced.

#### **2.1.1 Mechanism and Utility**

From a utilitarian perspective, PE mimics the behavior of traditional expert systems where the decision is paramount. In scenarios requiring low latency, PE is advantageous because the token generation for the label is immediate. Furthermore, for tasks where the "ground truth" reasoning is implicit or intuitive (e.g., identifying code style violations), post-hoc explanation can be sufficient for human understanding.2  
However, the critical flaw in PE lies in its causal decoupling. Because the explanation is generated *after* the prediction, it is conditioned on the prediction, not the other way around. The model is effectively asked to "justify this answer," regardless of whether the answer was derived through sound logic or a lucky guess.3 This leads to the phenomenon of **unfaithfulness**, where the explanation serves as a persuasive narrative rather than a transparent audit trail of the model's internal activations.

#### **2.1.2 The Faithfulness Gap**

Research by Turpin et al. (2023) and others has quantified this "faithfulness gap," identifying cases where self-explanations systematically misrepresent the true reasons for predictions.3 For example, in vulnerability detection, a model might correctly identify a SQL injection flaw. However, in the PE setting, the subsequent explanation might cite "improper input validation" (a plausible general reason) while the model actually attended to the presence of a specific, irrelevant keyword like admin\_query.5  
This discrepancy renders PE dangerous for security audits. If a developer relies on the explanation to fix the bug, they might implement a validation check that satisfies the *explanation* but fails to address the *actual* root cause (e.g., lack of parameterized queries) that triggered the model's flag. The literature categorizes these hallucinations as "plausible but unfaithful," creating a false sense of security.4

### **2.2 The Explain-Then-Predict (EP) Paradigm: Ante-Hoc Reasoning**

The Explain-Then-Predict (EP) paradigm, popularized by the Chain-of-Thought (CoT) movement, reverses the generation order.1 The prompt explicitly instructs the model to "think step-by-step" or generate a reasoning trace *before* producing the final answer.

#### **2.2.1 The Computation-in-Context Hypothesis**

The theoretical advantage of EP is grounded in the autoregressive nature of Transformer models. LLMs generate tokens sequentially, with each token conditioning the probability distribution of subsequent tokens. By forcing the generation of a reasoning trace first, the model effectively "computes" intermediate states and places them into its context window.6  
When the model finally generates the prediction, it is conditioned on this explicit logical path. This process, often termed "computation-in-context," allows the model to break down complex problems—such as tracing the taint propagation of a variable in C++ code—into manageable sub-problems.7 The reasoning trace acts as a scratchpad, reducing the cognitive load required for the final inference step.

#### **2.2.2 Superiority in Logic-Intensive Tasks**

Empirical studies consistently demonstrate that EP outperforms PE in tasks requiring multi-step reasoning, such as symbolic logic, arithmetic, and software vulnerability detection.1 In the domain of software engineering, code is inherently structural and logical. A vulnerability is rarely a surface feature; it is a condition resulting from the interaction of data and control flow. EP allows the model to simulate this execution flow (e.g., "The variable x enters the function here, is modified there, and reaches the exec command without sanitization...") before concluding "Vulnerable".10  
Table 1 summarizes the comparative attributes of these paradigms based on the surveyed literature.

| Feature | Predict-Then-Explain (PE) | Explain-Then-Predict (EP) |
| :---- | :---- | :---- |
| **Order** | Prediction $\\rightarrow$ Explanation | Explanation $\\rightarrow$ Prediction |
| **Cognitive Analogy** | Rationalization / Justification | Reasoning / Planning |
| **Primary Risk** | Unfaithfulness (Hallucination) | Error Propagation (Wrong reasoning leads to wrong answer) |
| **Latency** | Low (for prediction) | High (prediction requires full explanation first) |
| **Accuracy (SE)** | Lower for complex bugs 9 | Higher for complex logic 11 |
| **Faithfulness** | Low correlation with internal state 3 | Higher causal link to prediction 12 |

### **2.3 Rationalization vs. Reasoning: A Nuanced Distinction**

It is crucial to distinguish between "rationalization" and "reasoning" in the context of your empirical study.

* **Rationalization** is backward-looking. It assumes the answer is known (or already decided) and seeks to fit a narrative to it. The literature indicates this is useful for documentation generation (e.g., "Explain what this code does") but detrimental for discovery tasks.13  
* **Reasoning** is forward-looking. It derives the answer from the premises. However, researchers caution that LLM "reasoning" is a simulation. As noted in discussions on model architecture, human reasoning itself is often a post-hoc rationalization of subconscious processes.14 Yet, in the context of *utility*, the EP paradigm forces the model to display a logical path that a human can verify, which is the gold standard for "usefulness" in SE tasks.15

---

## **3\. Vulnerability Detection: The Case for Structured Reasoning**

Vulnerability detection (VD) represents the "hard case" for explanation prompting. Unlike general code summarization, VD requires the identification of subtle, context-dependent flaws that may span multiple lines or functions. The literature indicates that standard LLMs often struggle with this, achieving low accuracy when prompted directly.9 The evolution from standard CoT to specialized frameworks like **R2Vul** illustrates the necessity of the explain-before design.

### **3.1 Limitations of Unstructured Chain-of-Thought**

While standard CoT ("Let's think step by step") improves performance over zero-shot baselines, it remains prone to unstructured drifting. In VD, an LLM using standard CoT might ramble about general coding best practices without pinpointing the specific line causing the exploit. Studies show that generic CoT prompts can lead to "hallucination of vulnerability," where the model constructs a valid-sounding argument for a bug that doesn't exist, simply because the function *looks* complex.16  
Furthermore, unstructured CoT often fails to capture the specific security semantics required for VD, such as Common Weakness Enumeration (CWE) categories or data-flow path constraints. The reasoning becomes a "word salad" of security terminology rather than a precise audit.17

### **3.2 The R2Vul Framework: State-of-the-Art in Explain-Before**

The most compelling evidence for the efficacy of explain-before prompting in VD comes from the **R2Vul** (Reasoning to Vulnerability) framework.10 This system does not merely ask the model to explain; it *trains* the model to value valid reasoning over plausible-but-flawed reasoning.

#### **3.2.1 Architecture and Methodology**

R2Vul utilizes a teacher-student distillation process combined with Reinforcement Learning from AI Feedback (RLAIF). The architecture is designed to explicitly maximize the "faithfulness" and "usefulness" of the generated explanation.

1. **Teacher Generation:** A large, capable model (e.g., GPT-4 or a 32B Code model) generates "reasoning traces" for a dataset of vulnerable functions. Crucially, it generates **contrastive pairs**:  
   * *Valid Reasoning:* A trace correctly identifying the bug and linking it to the ground truth CWE.  
   * *Flawed Reasoning:* A trace where the model is forced (via prompting) to hallucinate a justification for the *wrong* label (e.g., explaining why vulnerable code is safe, or vice versa).19  
2. **Preference Optimization (ORPO):** The student model (often a smaller, more efficient 1.5B or 7B model) is trained using Odds Ratio Preference Optimization. It learns to distinguish between the valid reasoning trace and the flawed one. This step is vital: it teaches the model *not just how to reason*, but *how to identify deceptive reasoning*.10

#### **3.2.2 Prompt Templates for R2Vul**

For your validation study, adopting the R2Vul prompt structure is highly recommended as it represents the current best practice for "explain-before" in security contexts. The prompts are **class-specific**, grounding the model in the expected security context.

* **Vulnerable Function Prompt:**  
  * *Template:* "The following function has been flagged as vulnerable. Input function: {code}. This function contains a vulnerability associated with the following CWE: {cwe\_list}. Explain the vulnerability by identifying the specific code constructs, the underlying mechanism, and the potential impact.".10  
  * *Mechanism:* This prompt forces the model to perform **grounded reasoning**. By injecting the CWE (in a training or few-shot context), the model's CoT is constrained to the definition of that specific weakness, preventing generic hallucinations.  
* **Non-Vulnerable Function Prompt:**  
  * *Template:* "This function has been reviewed and determined to not contain any known vulnerabilities. Given this information, generate a detailed and coherent thought process... 1\. Analysis of Code Safety... 2\. Absence of Common Vulnerabilities... 3\. Validation of the Non-Vulnerable Label.".20  
  * *Mechanism:* This "negative constraint" is equally important. It forces the model to prove safety through evidence (e.g., "The input is sanitized here"), rather than simply defaulting to "Safe."

#### **3.2.3 Empirical Results**

The results of R2Vul validate the EP paradigm. A 1.5B parameter model trained with this structured reasoning distillation outperformed its own 32B teacher and commercial models like Claude-Opus on specific VD benchmarks.10 This demonstrates that **structured, trained reasoning** (quality of the prompt/data) is a more significant factor in performance than model size (scale).

### **3.3 Structured Reasoning Distillation**

The success of R2Vul highlights a broader trend: **Structured Reasoning Distillation**. The explanation is not just a byproduct; it is the *primary artifact* used to align the model. By treating the explanation as a structured object (Analysis $\\rightarrow$ Mechanism $\\rightarrow$ Impact), the model learns a "security mindset" that standard PE prompting cannot achieve.10  
---

## **4\. Code Generation: The Role of Structured Chain-of-Thought (SCoT)**

In code generation, the "explain-before" paradigm takes on a different form. Here, the "explanation" is effectively a design plan or pseudocode. The challenge is that natural language is ambiguous, while code is rigid. Standard CoT often produces high-level descriptions that fail to translate into syntactically correct code.22

### **4.1 Structured Chain-of-Thought (SCoT)**

To bridge the gap between natural language reasoning and executable code, Li et al. (2023) proposed **Structured Chain-of-Thought (SCoT)**. This prompting technique explicitly constrains the reasoning process to follow the fundamental control structures of programming: Sequences, Branches, and Loops.11

#### **4.1.1 The Three Pillars of SCoT**

SCoT prompts ask the LLM to generate a "rough solving process" using three specific keys:

1. **Sequence:** Forces the model to linearize its logic (e.g., "Step 1: Initialize variable X"). This prevents the model from referencing variables before they are defined, a common hallucination in standard CoT.  
2. **Branch:** Forces explicit conditional logic (e.g., "If condition A is met, then... else..."). This ensures edge cases are considered *during the planning phase*, rather than being patched in later.24  
3. **Loop:** Forces the definition of iteration bounds (e.g., "While list is not empty..."). This reduces infinite loop errors and off-by-one errors.26

#### **4.1.2 SCoT Prompt Template**

For your study, the SCoT prompt template serves as the "treatment" condition for the Explain-Before design in code generation tasks.  
**Canonical SCoT Prompt:**  
"Please understand the requirement and write a rough solving process. It starts with an input-output structure. You should use three basic structures to build the solving process, including sequences, branches, and loops. The necessary details should be written in natural languages." 27  
**Example Output Structure:**

* **Input:** list of integers. **Output:** int.  
* **Sequence:** Initialize max\_val to \-infinity.  
* **Loop:** Iterate through each item in list:  
  * **Branch:** If item \> max\_val:  
    * **Sequence:** Set max\_val \= item.  
* **Sequence:** Return max\_val.

#### **4.1.3 Performance Gains**

Empirical evaluations on the HumanEval and MBPP benchmarks demonstrate that SCoT prompting significantly outperforms standard CoT. Specifically, SCoT achieved up to a **13.79% improvement in Pass@1** accuracy.25 This result supports the hypothesis that aligning the *structure* of the explanation with the *structure* of the target domain (code) enhances the model's ability to generate correct solutions.

### **4.2 Comparing SCoT to Other Prompting Methods**

Table 2 illustrates the landscape of prompting strategies for code generation, highlighting the trade-offs between flexibility and structure.

| Method | Description | Strengths | Weaknesses |
| :---- | :---- | :---- | :---- |
| **Zero-Shot** | Direct code generation. | Fastest inference. | prone to logical errors; lacks planning. |
| **Chain-of-Thought (CoT)** | "Think step by step." | Better than Zero-Shot; explicit planning. | NL ambiguity; reasoning may not map to code syntax.22 |
| **Structured CoT (SCoT)** | "Use Sequence/Branch/Loop." | high constraints; improved correctness.25 | Requires specific prompt engineering; may limit creativity. |
| **Program-of-Thought (PoT)** | Generate intermediate code (e.g., Python) to solve reasoning. | Executable reasoning; precise. | Computationally expensive; requires external interpreter.29 |

---

## **5\. Evaluating Explanation Quality: Faithfulness and Usefulness**

Validating your "explain-before" prompt design requires a rigorous evaluation methodology. The literature identifies two primary orthogonal dimensions of explanation quality: **Usefulness** (utility to the human user) and **Faithfulness** (alignment with the model's internal process).15

### **5.1 Faithfulness: The Holy Grail of XAI**

Faithfulness measures the extent to which the explanation accurately reflects the true cause of the model's prediction. A highly useful explanation (e.g., a clear, concise summary) might be unfaithful (e.g., a simplified lie).

#### **5.1.1 The Faithfulness Paradox**

The literature highlights a "Faithfulness Paradox": users often prefer explanations that are *less* faithful but *more* plausible.12 For example, a model might predict code is vulnerable based on a complex, non-linear interaction of weights. A faithful explanation would be unintelligible math. A useful explanation is "Missing null check on line 10." The goal of your study is to maximize usefulness without sacrificing the causal link that defines faithfulness.

#### **5.1.2 Measuring Faithfulness: Perturbation Metrics**

To quantify faithfulness without access to the model's weights (black-box evaluation), **Perturbation Testing** is the standard.30

* **Fidelity (Fid) / Sufficiency:** This metric assesses whether the explanation identifies the "sufficient" causes. If the explanation claims "Token A" is the cause, then removing "Token A" from the input should change the prediction.  
* **Protocol:**  
  1. Generate explanation $E$ and prediction $P$.  
  2. Extract key tokens $T$ identified in $E$.  
  3. Create perturbed input $I'$ by masking $T$.  
  4. Measure $\\Delta P$ (Change in prediction confidence). High $\\Delta P$ implies High Faithfulness.31

#### **5.1.3 Consistency Checks (R2Vul Approach)**

Another approach used in R2Vul is **Semantic Consistency**. If a model's reasoning trace concludes "The code is safe," but the final prediction is "Vulnerable," the explanation is inherently unfaithful (hallucinated).

* **Detection:** This can be automated using a "Judge LLM" to parse the explanation text and compare its semantic sentiment with the final label.32

### **5.2 Usefulness: Rubric-Based Human Evaluation**

Measuring usefulness requires human judgment. However, simple Likert scales ("Rate 1-5") are notoriously noisy and subjective. The **Rubrik's CUBE** framework represents the current gold standard for evaluating LLM explanations.33

#### **5.2.1 The Rubrik's CUBE Hierarchy**

Rubrik's CUBE introduces a hierarchical typology of explanations, ensuring that evaluation matches the *intent* of the text.33

1. **Commentary:** The baseline level. Does the explanation describe *what* is happening?  
   * *Components:* Action, Reason.  
   * *Dimensions:* Grammaticality, Conciseness.  
2. **Justification:** The intermediate level. Does the explanation explain *why* it is correct?  
   * *Components:* Evidence (citing specific code lines), Plausibility.  
   * *Dimensions:* Coherence, Appropriateness.34  
3. **Argument:** The highest level. Does the explanation *persuade* the user of the stance?  
   * *Components:* Stance Clarity (unambiguous decision), Affective Appeal.33

#### **5.2.2 Key Dimensions for Evaluation**

* **Stance Clarity:** Critical for vulnerability detection. An explanation that hedges ("This might be a bug...") is low utility. R2Vul emphasizes clear, evidence-based stances.33  
* **Plausibility vs. Truthfulness:** Evaluators must distinguish between "This sounds right" (Plausibility) and "This is factually accurate" (Truthfulness). The rubric explicitly separates these to identify "confident hallucinations".36

#### **5.2.3 Developer Study Protocol**

To validate usefulness, your study should replicate the protocols found in high-quality developer studies.37

* **Participants:** A mix of students (novices) and professionals. Research shows students value "readability" (Commentary), while experts value "conciseness" and "evidence" (Justification).38  
* **Task:** Bug localization or Code Review.  
* **Conditions:**  
  * Control: Code only.  
  * Treatment A: PE Explanation (Post-hoc).  
  * Treatment B: EP/SCoT Explanation (Ante-hoc).  
* **Metrics:** Task completion time, Accuracy of human review, and subjective rating using the Rubrik's CUBE dimensions.

---

## **6\. Empirical Study Design: Validating Explain-Before**

Based on the synthesis of the literature, the following experimental design is proposed to validate your explain-before prompt design against established research.

### **6.1 Research Questions**

1. **RQ1 (Faithfulness):** Does the Explain-Then-Predict (SCoT/R2Vul) paradigm produce explanations with higher Fidelity (perturbation impact) than Predict-Then-Explain?  
2. **RQ2 (Performance):** Does structured reasoning (SCoT) improve F1 scores in Vulnerability Detection and Pass@1 in Code Generation compared to unstructured CoT?  
3. **RQ3 (Usefulness):** Do human developers rate SCoT-generated explanations as more useful (based on Rubrik's CUBE) for bug fixing tasks?

### **6.2 Dataset Selection**

* **Vulnerability Detection:** Use the **MSR (Big-Vul)** or **CVEFixes** datasets. These provide ground truth labels and, crucially, CVE descriptions that act as "gold standard" explanations for reference.39  
* **Code Generation:** Use **HumanEval** or **MBPP**. These are the standard benchmarks for validating SCoT.25

### **6.3 Prompt Engineering Strategy**

You should implement three distinct prompt conditions:

1. **Baseline (PE):** "Classify this code as vulnerable or safe. Then, explain your decision."  
2. **Unstructured CoT (EP):** "Let's think step by step. Analyze the code for vulnerabilities. Finally, provide a classification."  
3. **Structured CoT (SCoT/R2Vul):**  
   * *For VD:* Use the R2Vul template: "Analyze Code Safety... Absence of Vulnerabilities... Validation of Label.".20  
   * *For Code Gen:* Use the SCoT template: "Use Sequence, Branch, and Loop structures to build a solving process.".27

### **6.4 Evaluation Protocol**

1. **Automated Evaluation:**  
   * Calculate F1/Pass@1 for all conditions.  
   * Run Perturbation Tests (Fidelity) on a random sample of 500 instances.  
   * Use an LLM-as-a-Judge (e.g., GPT-4o) to grade 1,000 explanations using the Rubrik's CUBE criteria (Stance Clarity, Coherence, Evidence).40  
2. **Human Evaluation:**  
   * Recruit 20+ developers (mix of experience levels).  
   * Present "blind" explanation pairs (PE vs. SCoT) for the same code snippet.  
   * Ask participants to select the "more useful" explanation and rate it on the Rubrik's CUBE dimensions.38

---

## **7\. Conclusion and Future Outlook**

The aggregation of recent research strongly suggests that the "Explain-Before" paradigm is not merely a stylistic preference but a structural necessity for reliable neural software engineering. The limitations of the "Predict-Then-Explain" model—specifically its propensity for plausible but unfaithful hallucinations—disqualify it for high-assurance tasks like vulnerability detection.  
By contrast, the "Explain-Then-Predict" approach, particularly when augmented with **Structured Chain-of-Thought (SCoT)** and **Reinforcement Learning (R2Vul)**, aligns the model's generative process with the logical rigor of software development. The SCoT framework's use of programming primitives (Sequence, Branch, Loop) serves as a cognitive bridge, translating the model's probabilistic nature into deterministic code logic. Similarly, R2Vul's contrastive training demonstrates that models can be explicitly aligned to value valid reasoning over deceptive plausibility.  
For your empirical study, the integration of the **Rubrik's CUBE** for evaluation and **Perturbation Metrics** for faithfulness will provide a robust, multi-dimensional validation of your prompt design. As the field advances, we anticipate a convergence of these methods into "Neuro-Symbolic" architectures, where the "explanation" is an executable specification that can be formally verified, closing the loop between probabilistic generation and logical correctness.  
---

## **8\. Appendix: Detailed Research Synthesis**

### **8.1 Comparative Analysis of Prompting Strategies**

| Feature | Vanilla / Zero-Shot | Predict-Then-Explain (PE) | Chain-of-Thought (CoT) | Structured CoT (SCoT) | R2Vul (RLAIF \+ CoT) |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Core Mechanism** | Direct Mapping | Prediction $\\rightarrow$ Rationalization | Reasoning $\\rightarrow$ Prediction | Structured Plan $\\rightarrow$ Code | Contrastive Reasoning $\\rightarrow$ Preference Opt. |
| **Faithfulness** | N/A | Low (Post-hoc) | Moderate (Ante-hoc) | High (Constrained) | Highest (Optimized) |
| **Code Gen Pass@1** | Baseline | N/A | \+0.82% over Baseline 41 | \+13.79% over CoT 25 | N/A |
| **Vuln Detect F1** | \~0.60 9 | Similar to Baseline | Improved 9 | High Precision | SOTA (beats comm. LLMs) 21 |
| **Reasoning Style** | None | Free-text justification | Free-text narrative | Pseudo-code (Seq/Branch/Loop) | Security-grounded (CWE/CVE) |

### **8.2 Summary of Key Literature Clusters**

* **The Faithfulness Gap:** Extensive evidence exists that PE leads to unfaithful explanations where the model "makes up" reasons to fit the answer.3  
* **Structure Matters:** In code generation, the *format* of the reasoning (SCoT) is as important as the content. Aligning reasoning with code topology (sequences, loops) drastically reduces logic errors.23  
* **Training for Reasoning:** R2Vul proves that "reasoning" is a learnable skill. By distilling structured reasoning from a teacher model and using RLAIF, smaller models can outperform larger ones.10  
* **Evaluation rigor:** Simple Likert scales are insufficient. Hierarchical rubrics like Rubrik's CUBE provide the necessary granularity to distinguish "Commentary" from "Justification" and "Argument".33

### **8.3 Implications for Your Study**

To validate your explain-before design effectively:

1. **Do not rely on PE as a "strong" baseline.** The literature treats it as a flawed methodology for reasoning tasks. Use it to demonstrate the "faithfulness gap."  
2. **Adopt the SCoT syntax.** Do not just ask for "reasoning"; ask for "sequences, branches, and loops." This is the differentiating factor in recent high-performance benchmarks.27  
3. **Use Class-Specific Prompts.** Follow the R2Vul example of using different templates for "Vulnerable" vs. "Safe" code to ground the reasoning in the appropriate context.10

#### **Works cited**

1. Faithfulness of LLM Self-Explanations for Commonsense Tasks: Larger Is Better, and Instruction-Tuning Allows Trade-Offs but Not Pareto Dominance \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2503.13445v1](https://arxiv.org/html/2503.13445v1)  
2. Explainability in Language Models | PDF | Machine Learning \- Scribd, accessed November 22, 2025, [https://www.scribd.com/document/669616422/2309-01029](https://www.scribd.com/document/669616422/2309-01029)  
3. Verbosity Tradeoffs and the Impact of Scale on the Faithfulness of LLM Self-Explanations, accessed November 22, 2025, [https://arxiv.org/html/2503.13445v2](https://arxiv.org/html/2503.13445v2)  
4. VERBOSITY TRADEOFFS AND THE IMPACT OF SCALE ON THE FAITHFULNESS OF LLM SELF-EXPLANATIONS \- OpenReview, accessed November 22, 2025, [https://openreview.net/pdf?id=88UhuL0QSd](https://openreview.net/pdf?id=88UhuL0QSd)  
5. Measuring Faithfulness in Chain-of-Thought Reasoning | Anthropic, accessed November 22, 2025, [https://www-cdn.anthropic.com/827afa7dd36e4afbb1a49c735bfbb2c69749756e/measuring-faithfulness-in-chain-of-thought-reasoning.pdf](https://www-cdn.anthropic.com/827afa7dd36e4afbb1a49c735bfbb2c69749756e/measuring-faithfulness-in-chain-of-thought-reasoning.pdf)  
6. Exploring Advanced Reasoning Techniques for LLMs: Chain-of-Thought (CoT), Step-by-Step Rationalization (STaR), and Tree of Thoughts (ToT) \- Privacy. Cryptography. Freedom., accessed November 22, 2025, [https://www.eddieoz.com/exploring-advanced-reasoning-techniques-for-llms-chain-of-thought-cot-step-by-step-rationalization-star-and-tree-of-thoughts-tot/](https://www.eddieoz.com/exploring-advanced-reasoning-techniques-for-llms-chain-of-thought-cot-step-by-step-rationalization-star-and-tree-of-thoughts-tot/)  
7. Benchmarking LLMs and LLM-based Agents in Practical Vulnerability Detection for Code Repositories \- Yebo Feng, accessed November 22, 2025, [https://yebof.github.io/assets/pdf/yildiz2025acl.pdf](https://yebof.github.io/assets/pdf/yildiz2025acl.pdf)  
8. Prompt Engineering Techniques | IBM, accessed November 22, 2025, [https://www.ibm.com/think/topics/prompt-engineering-techniques](https://www.ibm.com/think/topics/prompt-engineering-techniques)  
9. A Comparative Evaluation of Large Language Models in Vulnerability Detection, accessed November 22, 2025, [https://www.ndss-symposium.org/wp-content/uploads/2025-1491-paper.pdf](https://www.ndss-symposium.org/wp-content/uploads/2025-1491-paper.pdf)  
10. R2Vul: Learning to Reason about Software Vulnerabilities with Reinforcement Learning and Structured Reasoning Distillation \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2504.04699v2](https://arxiv.org/html/2504.04699v2)  
11. Specification-Guided Vulnerability Detection with Large Language Models \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2511.04014](https://arxiv.org/html/2511.04014)  
12. R2Vul: Learning to Reason about Software Vulnerabilities with Reinforcement Learning and Structured Reasoning Distillation | alphaXiv, accessed November 22, 2025, [https://www.alphaxiv.org/overview/2504.04699v2](https://www.alphaxiv.org/overview/2504.04699v2)  
13. STaR: Self-Taught Reasoner \- OpenReview, accessed November 22, 2025, [https://openreview.net/pdf?id=\_3ELRdg2sgI](https://openreview.net/pdf?id=_3ELRdg2sgI)  
14. The "Reasoning" in LLMs might not be the actual reasoning, but why realise it now? \- Reddit, accessed November 22, 2025, [https://www.reddit.com/r/LocalLLaMA/comments/1kr16pq/the\_reasoning\_in\_llms\_might\_not\_be\_the\_actual/](https://www.reddit.com/r/LocalLLaMA/comments/1kr16pq/the_reasoning_in_llms_might_not_be_the_actual/)  
15. Faithfulness | DeepEval \- The Open-Source LLM Evaluation Framework, accessed November 22, 2025, [https://deepeval.com/docs/metrics-faithfulness](https://deepeval.com/docs/metrics-faithfulness)  
16. Are They All Good? Evaluating the Quality of CoTs in LLM-based Code Generation \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2507.06980v1](https://arxiv.org/html/2507.06980v1)  
17. Benchmarking Dataset for Static Code Analyzers and LLMs towards CWE Detection \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2503.09433v1](https://arxiv.org/html/2503.09433v1)  
18. (PDF) R2Vul: Learning to Reason about Software Vulnerabilities with Reinforcement Learning and Structured Reasoning Distillation \- ResearchGate, accessed November 22, 2025, [https://www.researchgate.net/publication/390570963\_R2Vul\_Learning\_to\_Reason\_about\_Software\_Vulnerabilities\_with\_Reinforcement\_Learning\_and\_Structured\_Reasoning\_Distillation](https://www.researchgate.net/publication/390570963_R2Vul_Learning_to_Reason_about_Software_Vulnerabilities_with_Reinforcement_Learning_and_Structured_Reasoning_Distillation)  
19. R2Vul: Learning to Reason about Software Vulnerabilities with Reinforcement Learning and Structured Reasoning Distillation \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2504.04699v1](https://arxiv.org/html/2504.04699v1)  
20. R2Vul: Learning to Reason about Software Vulnerabilities with Reinforcement Learning and Structured Reasoning Distillation \- arXiv, accessed November 22, 2025, [https://arxiv.org/pdf/2504.04699](https://arxiv.org/pdf/2504.04699)  
21. \[2504.04699\] R2Vul: Learning to Reason about Software Vulnerabilities with Reinforcement Learning and Structured Reasoning Distillation \- arXiv, accessed November 22, 2025, [https://arxiv.org/abs/2504.04699](https://arxiv.org/abs/2504.04699)  
22. Whispering to LLMs: The Art of Prompt Engineering and Unleashing LLM's Potential, accessed November 22, 2025, [https://medium.com/@263akash/whispering-to-llms-the-art-of-prompt-engineering-and-unleashing-llms-potential-93f2a205391b](https://medium.com/@263akash/whispering-to-llms-the-art-of-prompt-engineering-and-unleashing-llms-potential-93f2a205391b)  
23. A Preliminary Study on Large Language Models Self-Negotiation in, accessed November 22, 2025, [https://www.computer.org/csdl/proceedings-article/icsme/2025/958700a833/2bgfPcs70fm](https://www.computer.org/csdl/proceedings-article/icsme/2025/958700a833/2bgfPcs70fm)  
24. Aman's AI Journal • Primers • Prompt Engineering, accessed November 22, 2025, [https://aman.ai/primers/ai/prompt-engineering/](https://aman.ai/primers/ai/prompt-engineering/)  
25. Code Vulnerability Repair with Large Language Model Using Context-Aware Prompt Tuning, accessed November 22, 2025, [https://www.researchgate.net/publication/393389800\_Code\_Vulnerability\_Repair\_with\_Large\_Language\_Model\_Using\_Context-Aware\_Prompt\_Tuning](https://www.researchgate.net/publication/393389800_Code_Vulnerability_Repair_with_Large_Language_Model_Using_Context-Aware_Prompt_Tuning)  
26. A Systematic Survey of Prompt Engineering in Large Language Models: Techniques and Applications \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2402.07927v1](https://arxiv.org/html/2402.07927v1)  
27. Structured Chain-of-Thought Prompting for Code Generation \- arXiv, accessed November 22, 2025, [https://arxiv.org/pdf/2305.06599](https://arxiv.org/pdf/2305.06599)  
28. Structured Chain-of-Thought Prompting for Code Generation \- Ge Li, accessed November 22, 2025, [https://ligechina.github.io/My%20Papers/2025%20-%20TOSEM%20-%20Structured%20Chain-of-Thought%20Prompting%20for%20Code%20Generation.pdf](https://ligechina.github.io/My%20Papers/2025%20-%20TOSEM%20-%20Structured%20Chain-of-Thought%20Prompting%20for%20Code%20Generation.pdf)  
29. Large Language Model Reasoning Process and Prompting techniques Part 2 | by Xin Cheng, accessed November 22, 2025, [https://billtcheng2013.medium.com/large-language-model-reasoning-process-and-prompting-techniques-part-2-f048d6e7e76f](https://billtcheng2013.medium.com/large-language-model-reasoning-process-and-prompting-techniques-part-2-f048d6e7e76f)  
30. F-Fidelity: A Robust Framework for Faithfulness Evaluation of Explainable AI \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2410.02970v2](https://arxiv.org/html/2410.02970v2)  
31. A Causal Lens for Evaluating Faithfulness Metrics \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2502.18848v1](https://arxiv.org/html/2502.18848v1)  
32. VULPO: Context-Aware Vulnerability Detection via On-Policy LLM Optimization \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2511.11896v2](https://arxiv.org/html/2511.11896v2)  
33. Testing a New Rubric for Evaluating Explanations on the CUBE dataset \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2503.23899v2](https://arxiv.org/html/2503.23899v2)  
34. Testing a New Rubric for Evaluating Explanations on the CUBE dataset \- arXiv, accessed November 22, 2025, [https://arxiv.org/html/2503.23899v1](https://arxiv.org/html/2503.23899v1)  
35. Rubrik's Cube: Testing a New Rubric for Evaluating Explanations on the CUBE dataset \- ACL Anthology, accessed November 22, 2025, [https://aclanthology.org/2025.acl-long.1160.pdf](https://aclanthology.org/2025.acl-long.1160.pdf)  
36. Rubrik's Cube: Testing a New Rubric for Evaluating Explanations on the CUBE dataset \- OpenReview, accessed November 22, 2025, [https://openreview.net/pdf?id=hexvVmn0ur](https://openreview.net/pdf?id=hexvVmn0ur)  
37. Explaining Software Bugs Leveraging Code Structures in Neural Machine Translation, accessed November 22, 2025, [https://arxiv.org/html/2212.04584v5](https://arxiv.org/html/2212.04584v5)  
38. (PDF) Can Developers Prompt? A Controlled Experiment for Code Documentation Generation \- ResearchGate, accessed November 22, 2025, [https://www.researchgate.net/publication/385378972\_Can\_Developers\_Prompt\_A\_Controlled\_Experiment\_for\_Code\_Documentation\_Generation](https://www.researchgate.net/publication/385378972_Can_Developers_Prompt_A_Controlled_Experiment_for_Code_Documentation_Generation)  
39. martin-wey/R2Vul: R2Vul: Learning to Reason about ... \- GitHub, accessed November 22, 2025, [https://github.com/martin-wey/R2Vul](https://github.com/martin-wey/R2Vul)  
40. Using Different Evaluation Metrics \- Future AGI Documentation, accessed November 22, 2025, [https://docs.futureagi.com/cookbook/optimization/eval-metrics-for-optimization](https://docs.futureagi.com/cookbook/optimization/eval-metrics-for-optimization)  
41. Structured Chain-of-Thought Prompting Enhances Code Generation with Large Language Models \- OpenReview, accessed November 22, 2025, [https://openreview.net/pdf/ceceb61f95927288d706abbb9e9193f358b81700.pdf](https://openreview.net/pdf/ceceb61f95927288d706abbb9e9193f358b81700.pdf)