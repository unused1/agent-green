# RQ3 — Qualitative FP/FN cases (rebuttal narrative)

Companion to `rq3_b5_cross_model_summary.md`. Selected to illustrate the *plausibly-worded but causally-disconnected* pattern that drives the statistical correct-vs-incorrect gap.

Selection: highest *plausibility-disconnect* score (`actionability + clarity − completeness − informativeness`) within each (model × error_type × response_mode) stratum, top 1 per stratum.

Each case shows the source code, the model's response, the LLM judge's justification for the two lowest-scoring dimensions, and a short analyst note. All cases are from the Super-49B or Qwen3-30B SA zero-shot incorrect-intersection pool.


## Nemotron-Super-49B


### Case: Nemotron-Super-49B · instruct · FN · entry_id=195388

**Ground truth**: vulnerable (model predicted safe)  

**CWE**: ['CWE-522']  

**CVE description**: A man-in-the-middle attacker can inject false responses to the client's first few queries, despite the use of SSL certificate verification and encryption.  

**Plausibility-disconnect score**: +2  

**Judge scores** — completeness 1, clarity 3, actionability 1, informativeness 1


**Source code (excerpt)**:

```c
PQconnectPoll(PGconn *conn)
{
	bool		reset_connection_state_machine = false;
	bool		need_new_connection = false;
	PGresult   *res;
	char		sebuf[PG_STRERROR_R_BUFLEN];
	int			optval;

	if (conn == NULL)
		return PGRES_POLLING_FAILED;

	/* Get the new data */
	switch (conn->status)
	{
			/*
			 * We really shouldn't have been polled in these two cases, but we
			 * can handle it.
			 */
		case CONNECTION_BAD:
			return PGRES_POLLING_FAILED;
		case CONNECTION_OK:
			return PGRES_POLLING_OK;

			/* These are reading states */
		case CONNECTION_AWAITING_RESPONSE:
		case CONNECTION_AUTH_OK:
		case CONNECTION_CHECK_WRITABLE:
		case CONNECTION_CONSUME:
		case CONNECTION_CHECK_STANDBY:
			{
// […]
```


**Model response (excerpt)**:

> **Security Analysis of Provided Code**  **Overview**  The provided code is a part of the libpq library, which is the PostgreSQL client library. The function `PQconnectPoll` manages the connection process to a PostgreSQL server, handling various states and potential errors.  **Step-by-Step Analysis**  1. **Input Validation**: 	* The function checks if `conn` is `NULL` at the beginning, preventing null pointer dereferences. 	* It validates the `conn->status` to ensure it's in a recognized state. 	* Hostnames, ports, and other connection parameters are validated (e.g., port number range check). […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The analysis completely misses the actual vulnerability (CWE-522). The CVE describes a man-in-the-middle attack where false responses can be injected to the client's first few queries despite SSL certificate verification. The critical issue is that after SSL negotiation completes and the connection transitions to CONNE […]

- *actionability* (score 1): The response concludes there is no vulnerability and provides no actionable guidance. It fails to identify the actual vulnerability, the specific code locations involved (the CONNECTION_CHECK_WRITABLE and CONNECTION_CHECK_STANDBY states where query results are trusted), or any remediation steps.


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis).


---


### Case: Nemotron-Super-49B · thinking · FN · entry_id=216903

**Ground truth**: vulnerable (model predicted safe)  

**CWE**: ['CWE-476']  

**CVE description**: MariaDB through 10.5.9 allows an application crash in sub_select_postjoin_aggr for a NULL value of aggr.  

**Plausibility-disconnect score**: +2  

**Judge scores** — completeness 1, clarity 3, actionability 1, informativeness 1


**Source code (excerpt)**:

```c
bool st_select_lex::optimize_unflattened_subqueries(bool const_only)
{
  SELECT_LEX_UNIT *next_unit= NULL;
  for (SELECT_LEX_UNIT *un= first_inner_unit();
       un;
       un= next_unit ? next_unit : un->next_unit())
  {
    Item_subselect *subquery_predicate= un->item;
    next_unit= NULL;

    if (subquery_predicate)
    {
      if (!subquery_predicate->fixed)
      {
	/*
	 This subquery was excluded as part of some expression so it is
	 invisible from all prepared expression.
       */
	next_unit= un->next_unit();
	un->exclude_level();
	if (next_unit)
	  continue;
	break;
      }
      if (subquery_predicate->substype() == Item_subselect::IN_SUBS)
      {
        Item_in_subselect *in_subs= (Item_in_subselect*) subquery_predicate;
        if (in_subs->is_jtbm_merged)
          continue;
      }
// […]
```


**Model response (excerpt)**:

> <think> Okay, let's take a look at this code. It's a C++ function called optimize_unflattened_subqueries in the st_select_lex class. The function seems to handle optimizing subqueries in a SQL query, possibly part of a database system like MySQL.  First, I need to check for any potential vulnerabilities. Common issues in C++ code could include memory leaks, buffer overflows, use of uninitialized variables, or issues with concurrency. But since this is static analysis, I should focus on code patterns that might lead to vulnerabilities.  Looking at the code structure: there's a loop over SELECT_ […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The response completely misses the actual vulnerability (CWE-476, NULL pointer dereference). The CVE describes a crash in sub_select_postjoin_aggr for a NULL value of aggr. The analysis incorrectly concludes the code is safe, failing to identify the specific NULL pointer dereference condition that leads to the applicat […]

- *actionability* (score 1): The response provides no actionable guidance since it incorrectly identifies the code as safe. No vulnerable lines are highlighted, no patches are suggested, and no specific risks related to the actual NULL pointer dereference vulnerability are described. A developer reading this would take no action on a genuinely vul […]


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis).


---


### Case: Nemotron-Super-49B · instruct · FP · entry_id=276993

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-703']  

**CVE description**: NULL Pointer Dereference in GitHub repository mruby/mruby prior to 3.2.  

**Plausibility-disconnect score**: +2  

**Judge scores** — completeness 2, clarity 4, actionability 2, informativeness 2


**Source code (excerpt)**:

```c
fiber_switch(mrb_state *mrb, mrb_value self, mrb_int len, const mrb_value *a, mrb_bool resume, mrb_bool vmexec)
{
  struct mrb_context *c = fiber_check(mrb, self);
  struct mrb_context *old_c = mrb->c;
  enum mrb_fiber_state status;
  mrb_value value;

  fiber_check_cfunc(mrb, c);
  status = c->status;
  switch (status) {
  case MRB_FIBER_TRANSFERRED:
    if (resume) {
      mrb_raise(mrb, E_FIBER_ERROR, "resuming transferred fiber");
    }
    break;
  case MRB_FIBER_RUNNING:
  case MRB_FIBER_RESUMED:
    mrb_raise(mrb, E_FIBER_ERROR, "double resume");
    break;
  case MRB_FIBER_TERMINATED:
    mrb_raise(mrb, E_FIBER_ERROR, "resuming dead fiber");
    break;
  default:
    break;
  }
  old_c->status = resume ? MRB_FIBER_RESUMED : MRB_FIBER_TRANSFERRED;
  c->prev = resume ? mrb->c : (c->prev ? c->prev : mrb->root_c);
  fiber_switch_context(mrb, c);
  if (status == MRB_FIBER_CREATED) {
    mrb_value *b, *e;
// […]
```


**Model response (excerpt)**:

> Let's analyze the provided code step-by-step to determine if there's a vulnerability.  **Code Overview**  The `fiber_switch` function appears to be part of a fiber (lightweight thread) implementation, likely for the MRuby programming language. It handles switching between fibers, managing their states, and executing their code.  **Step-by-Step Analysis**  1. **Input Validation**: 	* The function takes several inputs: `mrb`, `self`, `len`, `a` (an array of `mrb_value`), `resume`, and `vmexec`. 	* **No explicit validation** is performed on `len` or the contents of `a`. **Potential issue**, but l […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 2): The analysis incorrectly concludes there is a vulnerability when the ground truth indicates the code is safe. The response fails to recognize that mrb_stack_extend(mrb, len+2) properly allocates sufficient space before the copy loop, making the out-of-bounds write claim incorrect. The analysis of fiber state management […]

- *actionability* (score 2): The response identifies specific code locations and suggests bounds checking is needed, but since the code is actually safe, this actionability is misguided. The suggested remediation would be unnecessary work for a developer.


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong.


---


### Case: Nemotron-Super-49B · thinking · FP · entry_id=251946

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-369']  

**CVE description**: TensorFlow is an end-to-end open source platform for machine learning. In affected versions an attacker can craft a TFLite model that would trigger a null pointer dereference, which would result in a crash and denial of […]  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 2, clarity 4, actionability 3, informativeness 2


**Source code (excerpt)**:

```c
inline void BinaryBroadcastFiveFold(const ArithmeticParams& unswitched_params,
                                    const RuntimeShape& unswitched_input1_shape,
                                    const T* unswitched_input1_data,
                                    const RuntimeShape& unswitched_input2_shape,
                                    const T* unswitched_input2_data,
                                    const RuntimeShape& output_shape,
                                    T* output_data, ElementwiseF elementwise_f,
                                    ScalarBroadcastF scalar_broadcast_f) {
  ArithmeticParams switched_params = unswitched_params;
  switched_params.input1_offset = unswitched_params.input2_offset;
  switched_params.input1_multiplier = unswitched_params.input2_multiplier;
  switched_params.input1_shift = unswitched_params.input2_shift;
  switched_params.input2_offset = unswitched_params.input1_offset;
  switched_params.input2_multiplier = unswitched_params.input1_multiplier;
  switched_params.input2_shift = unswitched_params.input1_shift;

  const bool use_unswitched =
      unswitched_params.broadcast_category ==
      tflite::BroadcastableOpCategory::kFirstInputBroadcastsFast;

  const ArithmeticParams& params =
      use_unswitched ? unswitched_params : switched_params;
  const T* input1_data =
      use_unswitched ? unswitched_input1_data : unswitched_input2_data;
  const T* input2_data =
      use_unswitched ? unswitched_input2_data : unswitched_input1_data;

  // Fivefold nested loops. The second input resets its position for each
  // iteration of the second loop. The first input resets its position at the
  // beginning of the fourth loop. The innermost loop is an elementwise add of
// […]
```


**Model response (excerpt)**:

> <think> Okay, let's take a look at this code. Hmm, the function is called BinaryBroadcastFiveFold, which suggests it's handling some kind of broadcasting operation in a binary operation, maybe like adding two tensors with different shapes. The code seems to be part of a machine learning framework, possibly TensorFlow Lite given the namespace tflite.  First, I need to check for any potential security vulnerabilities. Common issues in such code could be buffer overflows, use of uninitialized variables, or incorrect handling of input data leading to out-of-bounds accesses.  Looking at the paramet […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 2): The response identifies a potential null pointer dereference concern, but the ground truth indicates this code is safe. The analysis fails to recognize that the null check in the y4==1 branch is a defensive measure, not evidence of a vulnerability in the y4>1 branch. The function's contract likely requires valid (non-n […]

- *informativeness* (score 2): The response makes a superficial observation about asymmetric null checking between the two branches but fails to provide deeper insight into why this pattern exists or whether it actually constitutes a vulnerability. It doesn't consider that the null check in the y4==1 case might be a defensive/optional guard rather t […]


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong; still proposes remediation, just for the wrong underlying claim.


---


## Qwen3-30B-A3B


### Case: Qwen3-30B-A3B · instruct · FN · entry_id=216515

**Ground truth**: vulnerable (model predicted safe)  

**CWE**: ['CWE-362']  

**CVE description**: Race condition in the ssl3_get_new_session_ticket function in ssl/s3_clnt.c in OpenSSL before 0.9.8zg, 1.0.0 before 1.0.0s, 1.0.1 before 1.0.1n, and 1.0.2 before 1.0.2b, when used for a multi-threaded client, allows remo […]  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 1, clarity 4, actionability 1, informativeness 1


**Source code (excerpt)**:

```c
int ssl3_get_new_session_ticket(SSL *s)
{
    int ok, al, ret = 0, ticklen;
    long n;
    const unsigned char *p;
    unsigned char *d;

    n = s->method->ssl_get_message(s,
                                   SSL3_ST_CR_SESSION_TICKET_A,
                                   SSL3_ST_CR_SESSION_TICKET_B,
                                   SSL3_MT_NEWSESSION_TICKET, 16384, &ok);

    if (!ok)
        return ((int)n);

    if (n < 6) {
        /* need at least ticket_lifetime_hint + ticket length */
        al = SSL_AD_DECODE_ERROR;
        SSLerr(SSL_F_SSL3_GET_NEW_SESSION_TICKET, SSL_R_LENGTH_MISMATCH);
        goto f_err;
    }

    p = d = (unsigned char *)s->init_msg;
    n2l(p, s->session->tlsext_tick_lifetime_hint);
    n2s(p, ticklen);
    /* ticket_lifetime_hint + ticket_length + ticket */
    if (ticklen + 6 != n) {
        al = SSL_AD_DECODE_ERROR;
        SSLerr(SSL_F_SSL3_GET_NEW_SESSION_TICKET, SSL_R_LENGTH_MISMATCH);
        goto f_err;
// […]
```


**Model response (excerpt)**:

> Step 1: Analyze the code carefully   The function `ssl3_get_new_session_ticket` is part of OpenSSL's SSL/TLS implementation and handles the reception of a `NEWSESSION_TICKET` message from the server during the handshake. The function performs the following steps:  - It receives a message from the server using `ssl_get_message`, which reads data into `s->init_msg` and returns the length `n`. - It checks if the received data length `n` is at least 6 bytes (minimum required for `ticket_lifetime_hint` and `ticket_length`). - It parses `ticket_lifetime_hint` (4 bytes) and `ticket_length` (2 bytes) […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The response completely misses the actual vulnerability (CWE-362, race condition). The CVE describes a race condition in multi-threaded clients where the session object (s->session) may be shared across threads. When the function frees and reallocates tlsext_tick without creating a new session object first, another thr […]

- *actionability* (score 1): The response concludes the code is secure and provides no remediation guidance. Since the code is actually vulnerable, this is a critical failure in actionability — a developer reading this would take no action on a real vulnerability.


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong.


---


### Case: Qwen3-30B-A3B · thinking · FN · entry_id=195405

**Ground truth**: vulnerable (model predicted safe)  

**CWE**: ['CWE-190']  

**CVE description**: A vulnerability was found in ImageMagick, causing an outside the range of representable values of type 'unsigned long' at coders/pcl.c, when crafted or untrusted input is processed. This leads to a negative impact to app […]  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 1, clarity 4, actionability 1, informativeness 1


**Source code (excerpt)**:

```c
static Image *ReadPCLImage(const ImageInfo *image_info,ExceptionInfo *exception)
{
#define CropBox  "CropBox"
#define DeviceCMYK  "DeviceCMYK"
#define MediaBox  "MediaBox"
#define RenderPCLText  "  Rendering PCL...  "

  char
    command[MaxTextExtent],
    *density,
    filename[MaxTextExtent],
    geometry[MaxTextExtent],
    *options,
    input_filename[MaxTextExtent];

  const DelegateInfo
    *delegate_info;

  Image
    *image,
    *next_image;

  ImageInfo
    *read_info;

  int
    c;

  MagickBooleanType
    cmyk,
// […]
```


**Model response (excerpt)**:

> We are analyzing the provided code for potential vulnerabilities. The code is a function `ReadPCLImage` that reads a PCL (Printer Command Language) image file.  Key points to check for vulnerabilities in static analysis:  1. **Buffer Overflows**: Check for unsafe string operations (like `strcpy`, `sprintf`, `strcat`, etc.) that might lead to buffer overflows. 2. **Format String Vulnerabilities**: Check for `printf`-like functions that use user-controlled input as format strings. 3. **Integer Overflows**: Check for arithmetic operations that might overflow, leading to unexpected behavior. 4. ** […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The response concludes 'no vulnerability detected' despite the ground truth being CWE-190 (integer overflow). The analysis explicitly examines integer overflow but incorrectly dismisses it, claiming the double-to-size_t cast is safe. The critical vulnerability is precisely in lines like `width=(size_t) floor(bounds.x2- […]

- *actionability* (score 1): The response provides no actionable guidance because it incorrectly concludes there is no vulnerability. A developer reading this would be misled into thinking the code is safe, with no remediation suggested for the actual integer overflow issue.


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong.


---


### Case: Qwen3-30B-A3B · instruct · FP · entry_id=259732

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-703']  

**CVE description**: TensorFlow is an open source platform for machine learning. Prior to versions 2.9.0, 2.8.1, 2.7.2, and 2.6.4, the implementation of `tf.raw_ops.QuantizeAndDequantizeV4Grad` does not fully validate the input arguments. Th […]  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 3, clarity 5, actionability 4, informativeness 3


**Source code (excerpt)**:

```c
  void Compute(OpKernelContext* ctx) override {
    const Tensor& gradient = ctx->input(0);
    const Tensor& input = ctx->input(1);
    Tensor* input_backprop = nullptr;
    OP_REQUIRES_OK(ctx,
                   ctx->allocate_output(0, input.shape(), &input_backprop));
    OP_REQUIRES(
        ctx, axis_ >= -1,
        errors::InvalidArgument("Axis must be at least -1. Found ", axis_));
    OP_REQUIRES(ctx, (axis_ == -1 || axis_ < input.shape().dims()),
                errors::InvalidArgument(
                    "Axis should be -1 or 0 or a positive value less than ",
                    input.shape().dims(), "but given axis value was ", axis_));

    OP_REQUIRES(
        ctx, input.IsSameSize(gradient),
        errors::InvalidArgument("gradient and input must be the same size"));
    const int depth = (axis_ == -1) ? 1 : input.dim_size(axis_);
    const Tensor& input_min_tensor = ctx->input(2);
    OP_REQUIRES(ctx,
                input_min_tensor.dims() == 0 || input_min_tensor.dims() == 1,
                errors::InvalidArgument(
                    "Input min tensor must have dimension 0 or 1. Received ",
                    input_min_tensor.dims(), "."));
    const Tensor& input_max_tensor = ctx->input(3);
    OP_REQUIRES(ctx,
                input_max_tensor.dims() == 0 || input_max_tensor.dims() == 1,
                errors::InvalidArgument(
                    "Input max tensor must have dimension 0 or 1. Received ",
                    input_max_tensor.dims(), "."));
// […]
```


**Model response (excerpt)**:

> Let's analyze the provided code step by step to determine whether there is a security vulnerability.  ---  ### **1. Context and Purpose** This is a TensorFlow `OpKernel` implementation (likely for a quantization/dequantization gradient operation). It computes gradients for a quantized operation, with support for both per-tensor (axis = -1) and per-channel (axis >= 0) quantization.  Key inputs: - `gradient`: gradient tensor - `input`: input tensor - `input_min_tensor`: minimum value(s) for quantization - `input_max_tensor`: maximum value(s) for quantization  Outputs: - `input_backprop`: gradien […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 3): The analysis is thorough in examining most validation checks and tensor operations. However, it incorrectly identifies a vulnerability. In TensorFlow's Eigen tensor library, `flat_inner_outer_dims<T, 3>` with argument -1 is actually a valid and commonly used pattern — it means all dimensions are collapsed into the 'inn […]

- *informativeness* (score 3): The analysis demonstrates good understanding of TensorFlow kernel patterns, input validation, and tensor operations. It provides genuine technical depth in examining each validation check. However, the core insight about `flat_inner_outer_dims` with -1 being invalid is incorrect — this is a well-known Eigen pattern in […]


**Analyst note**: written confidently and cleanly despite being wrong; still proposes remediation, just for the wrong underlying claim.


---


### Case: Qwen3-30B-A3B · thinking · FP · entry_id=259732

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-703']  

**CVE description**: TensorFlow is an open source platform for machine learning. Prior to versions 2.9.0, 2.8.1, 2.7.2, and 2.6.4, the implementation of `tf.raw_ops.QuantizeAndDequantizeV4Grad` does not fully validate the input arguments. Th […]  

**Plausibility-disconnect score**: +4  

**Judge scores** — completeness 3, clarity 5, actionability 4, informativeness 2


**Source code (excerpt)**:

```c
  void Compute(OpKernelContext* ctx) override {
    const Tensor& gradient = ctx->input(0);
    const Tensor& input = ctx->input(1);
    Tensor* input_backprop = nullptr;
    OP_REQUIRES_OK(ctx,
                   ctx->allocate_output(0, input.shape(), &input_backprop));
    OP_REQUIRES(
        ctx, axis_ >= -1,
        errors::InvalidArgument("Axis must be at least -1. Found ", axis_));
    OP_REQUIRES(ctx, (axis_ == -1 || axis_ < input.shape().dims()),
                errors::InvalidArgument(
                    "Axis should be -1 or 0 or a positive value less than ",
                    input.shape().dims(), "but given axis value was ", axis_));

    OP_REQUIRES(
        ctx, input.IsSameSize(gradient),
        errors::InvalidArgument("gradient and input must be the same size"));
    const int depth = (axis_ == -1) ? 1 : input.dim_size(axis_);
    const Tensor& input_min_tensor = ctx->input(2);
    OP_REQUIRES(ctx,
                input_min_tensor.dims() == 0 || input_min_tensor.dims() == 1,
                errors::InvalidArgument(
                    "Input min tensor must have dimension 0 or 1. Received ",
                    input_min_tensor.dims(), "."));
    const Tensor& input_max_tensor = ctx->input(3);
    OP_REQUIRES(ctx,
                input_max_tensor.dims() == 0 || input_max_tensor.dims() == 1,
                errors::InvalidArgument(
                    "Input max tensor must have dimension 0 or 1. Received ",
                    input_max_tensor.dims(), "."));
// […]
```


**Model response (excerpt)**:

> We are analyzing the provided code for potential vulnerabilities. The code is a method `Compute` of an `OpKernel` in TensorFlow (or a similar framework). We are to check for security vulnerabilities, particularly in the context of static program analysis.  Key points to consider: 1. **Input Validation**: The code checks for various conditions on the inputs (like shape, dimensions, etc.) using `OP_REQUIRES` which will fail the operation if the condition is not met. This is a good practice to prevent invalid inputs from causing issues.  2. **Array Bounds and Indexing**: We need to check if there […]


**Judge justifications (lowest-scoring dimensions)**:

- *informativeness* (score 2): While the analysis demonstrates understanding of TensorFlow kernel patterns and provides detailed reasoning, the core technical claim is incorrect. The `flat_inner_outer_dims` function in TensorFlow does handle the -1 case correctly (it's a valid boundary condition). The false positive significantly undermines the info […]

- *completeness* (score 3): The analysis is detailed and examines multiple aspects of the code (input validation, memory allocation, scalar access). However, it incorrectly identifies a vulnerability in code that is actually safe. The analysis of `flat_inner_outer_dims` with `axis_ - 1 = -1` when `axis_ = 0` appears plausible but is incorrect — T […]


**Analyst note**: substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong; still proposes remediation, just for the wrong underlying claim.


---
