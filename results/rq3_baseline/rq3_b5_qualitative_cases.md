# RQ3 — Qualitative FP/FN cases (rebuttal narrative)

Companion to `rq3_b5_cross_model_summary.md`. Selected to illustrate the *plausibly-worded but causally-disconnected* pattern that drives the statistical correct-vs-incorrect gap.

Selection: highest *plausibility-disconnect* score (`actionability + clarity − completeness − informativeness`) within each (model × error_type × response_mode) stratum, top 1 per stratum.

Each case shows the source code, the model's response, the LLM judge's justification for the two lowest-scoring dimensions, and a short analyst note. All cases are from the Super-49B or Qwen3-30B SA zero-shot incorrect-intersection pool.


## Nemotron-Super-49B


### Case: Nemotron-Super-49B · instruct · FN · entry_id=216515

**Ground truth**: vulnerable (model predicted safe)  

**CWE**: ['CWE-362']  

**CVE description**: Race condition in the ssl3_get_new_session_ticket function in ssl/s3_clnt.c in OpenSSL before 0.9.8zg, 1.0.0 before 1.0.0s, 1.0.1 before 1.0.1n, and 1.0.2 before 1.0.2b, when used for a multi-threaded client, allows remo […]  

**Plausibility-disconnect score**: +4  

**Judge scores** — completeness 1, clarity 4, actionability 2, informativeness 1


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

> Let's analyze the provided code step-by-step for potential vulnerabilities:  **Code Overview** ----------------  The function `ssl3_get_new_session_ticket` appears to be part of an SSL/TLS implementation, specifically handling the reception of a new session ticket in the SSLv3/TLS protocol. The function processes the received ticket, extracts its components, and updates the session with the new ticket information.  **Step-by-Step Analysis** -------------------------  1. **Message Reception and Initial Checks**    - The function starts by receiving a message using `s->method->ssl_get_message`. […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The response completely misses the actual vulnerability (CWE-362, race condition). The CVE describes a race condition in multi-threaded clients where a NewSessionTicket during ticket reuse can cause a double free. The code modifies s->session directly without copying it first, meaning if the session is shared across th […]

- *informativeness* (score 1): The response fails to provide any meaningful insight about the actual vulnerability. It does not mention race conditions, double-free, multi-threading, or session sharing — all central to the CVE. The identified 'vulnerability' (unbounded ticklen) is not a real issue since the message size is already bounded by the 163 […]


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong.


---


### Case: Nemotron-Super-49B · thinking · FN · entry_id=216515

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

> <think> Okay, let's take a look at this code. It's a function called ssl3_get_new_session_ticket in OpenSSL. The function seems to handle receiving a new session ticket from the server during the SSL/TLS handshake. My task is to check if there's any vulnerability here.  First, I'll start by understanding the code flow. The function starts by calling s->method->ssl_get_message to get the message from the server. If that fails (ok is false), it returns n. Then it checks if the message length n is less than 6. If so, it sets an error and jumps to f_err.   Next, it processes the message data. The […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The response completely misses the actual vulnerability (CWE-362, race condition). The CVE describes a race condition in multi-threaded clients where a session being reused can be modified concurrently, leading to a double free. The analysis only examines sequential execution concerns (buffer overflows, input validatio […]

- *actionability* (score 1): The response declares no vulnerability exists, so it provides no remediation guidance. Since the code is actually vulnerable to a race condition, this is a false negative that provides no actionable information for addressing the real issue.


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong.


---


### Case: Nemotron-Super-49B · instruct · FP · entry_id=250692

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-552']  

**CVE description**: This affects the package drogonframework/drogon before 1.7.5. The unsafe handling of file names during upload using HttpFile::save() method may enable attackers to write files to arbitrary locations outside the designate […]  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 3, clarity 5, actionability 4, informativeness 3


**Source code (excerpt)**:

```c
int HttpFileImpl::saveAs(const std::string &fileName) const
{
    assert(!fileName.empty());
    filesystem::path fsFileName(utils::toNativePath(fileName));
    if (!fsFileName.is_absolute() && (!fsFileName.has_parent_path() ||
                                      (fsFileName.begin()->string() != "." &&
                                       fsFileName.begin()->string() != "..")))
    {
        filesystem::path fsUploadPath(utils::toNativePath(
            HttpAppFrameworkImpl::instance().getUploadPath()));
        fsFileName = fsUploadPath / fsFileName;
    }
    if (fsFileName.has_parent_path() &&
        !filesystem::exists(fsFileName.parent_path()))
    {
        LOG_TRACE << "create path:" << fsFileName.parent_path();
        drogon::error_code err;
        filesystem::create_directories(fsFileName.parent_path(), err);
        if (err)
        {
            LOG_SYSERR;
            return -1;
        }
    }
    return saveTo(fsFileName);
}
```


**Model response (excerpt)**:

> Let's analyze the provided C++ code step-by-step from a **static program analysis** and **security** perspective.  ---  ### 🔍 Code Overview  This is a method `saveAs` in a class `HttpFileImpl`. It appears to be part of a web framework (likely [Drogon](https://github.com/drogonframework/drogon)), handling the saving of an HTTP file to disk.  The function:  1. Converts the provided `fileName` to a filesystem path. 2. If the path is not absolute and doesn't have a parent path or starts with `.` or `..`, it prepends the upload path. 3. If the parent path of the file doesn't exist, it tries to crea […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 3): The analysis covers path traversal concerns in detail and examines multiple aspects of the code. However, the ground truth labels this as safe code, and the response incorrectly identifies a vulnerability. The analysis does trace through the logic carefully but misinterprets the intent: when the first component IS '..' […]

- *informativeness* (score 3): The analysis provides genuine technical depth about path traversal mechanics and the filesystem path API. However, the core conclusion is incorrect (false positive), which significantly diminishes the informativeness. The analysis of how the path components are checked is detailed but ultimately leads to a wrong conclu […]


**Analyst note**: written confidently and cleanly despite being wrong; still proposes remediation, just for the wrong underlying claim.


---


### Case: Nemotron-Super-49B · thinking · FP · entry_id=309831

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-787']  

**CVE description**: An issue was discovered in ncurses through v6.2-1. _nc_captoinfo in captoinfo.c has a heap-based buffer overflow.  

**Plausibility-disconnect score**: +2  

**Judge scores** — completeness 3, clarity 4, actionability 3, informativeness 2


**Source code (excerpt)**:

```c
cvtchar(register const char *sp)
/* convert a character to a terminfo push */
{
    unsigned char c = 0;
    int len;

    switch (*sp) {
    case '\\':
	switch (*++sp) {
	case '\'':
	case '$':
	case '\\':
	case '%':
	    c = UChar(*sp);
	    len = 2;
	    break;
	case '\0':
	    c = '\\';
	    len = 1;
	    break;
	case '0':
	case '1':
	case '2':
	case '3':
	    len = 1;
	    while (isdigit(UChar(*sp))) {
		c = UChar(8 * c + (*sp++ - '0'));
		len++;
	    }
	    break;
// […]
```


**Model response (excerpt)**:

> <think> Okay, let's take a look at this code. Hmm, the function is called cvtchar, and it's supposed to convert a character into some terminfo push. The code seems to handle various escape sequences and different cases for characters. I need to check for any possible vulnerabilities here.  First, the function starts by taking a pointer 'sp' which is a register const char. Then there's a switch on *sp. The first case is a backslash, which then has another switch on the next character. Let's see what happens here.  In the first case, when the first character is a backslash, it checks the next ch […]


**Judge justifications (lowest-scoring dimensions)**:

- *informativeness* (score 2): While the analysis demonstrates understanding of escape sequence parsing and provides detailed code walkthrough, the core insight is wrong. The backslash-null case is standard C string handling — the null terminator is not a 'character to consume' but the end of the string. The DoS concern about octal digit processing […]

- *completeness* (score 3): The analysis covers multiple aspects of the code including escape sequence handling, octal processing, and output generation. However, it incorrectly identifies the code as vulnerable when the ground truth says it's safe. The backslash-null handling is actually intentional — when a backslash is at the end of a string ( […]


**Analyst note**: substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong; still proposes remediation, just for the wrong underlying claim.


---


## Qwen3-30B-A3B


### Case: Qwen3-30B-A3B · instruct · FN · entry_id=214909

**Ground truth**: vulnerable (model predicted safe)  

**CWE**: ['CWE-401']  

**CVE description**: A memory leak in the mlx5_fpga_conn_create_cq() function in drivers/net/ethernet/mellanox/mlx5/core/fpga/conn.c in the Linux kernel before 5.3.11 allows attackers to cause a denial of service (memory consumption) by trig […]  

**Plausibility-disconnect score**: +2  

**Judge scores** — completeness 1, clarity 4, actionability 1, informativeness 2


**Source code (excerpt)**:

```c
static int mlx5_fpga_conn_create_cq(struct mlx5_fpga_conn *conn, int cq_size)
{
	struct mlx5_fpga_device *fdev = conn->fdev;
	struct mlx5_core_dev *mdev = fdev->mdev;
	u32 temp_cqc[MLX5_ST_SZ_DW(cqc)] = {0};
	u32 out[MLX5_ST_SZ_DW(create_cq_out)];
	struct mlx5_wq_param wqp;
	struct mlx5_cqe64 *cqe;
	int inlen, err, eqn;
	unsigned int irqn;
	void *cqc, *in;
	__be64 *pas;
	u32 i;

	cq_size = roundup_pow_of_two(cq_size);
	MLX5_SET(cqc, temp_cqc, log_cq_size, ilog2(cq_size));

	wqp.buf_numa_node = mdev->priv.numa_node;
	wqp.db_numa_node  = mdev->priv.numa_node;

	err = mlx5_cqwq_create(mdev, &wqp, temp_cqc, &conn->cq.wq,
			       &conn->cq.wq_ctrl);
	if (err)
		return err;

	for (i = 0; i < mlx5_cqwq_get_size(&conn->cq.wq); i++) {
		cqe = mlx5_cqwq_get_wqe(&conn->cq.wq, i);
		cqe->op_own = MLX5_CQE_INVALID << 4 | MLX5_CQE_OWNER_MASK;
	}

// […]
```


**Model response (excerpt)**:

> Step 1: Analyze the code carefully   The function `mlx5_fpga_conn_create_cq` is responsible for creating a Completion Queue (CQ) in an MLX5 FPGA connection context. It performs the following steps:   - Rounds up `cq_size` to the nearest power of two.   - Initializes a CQ context (`temp_cqc`) with the log size.   - Sets up a work queue parameter (`wqp`) with NUMA node information from the device.   - Creates a CQ work queue (`mlx5_cqwq_create`) using the provided parameters.   - Initializes CQE entries in the WQ to invalid state.   - Allocates memory for the `create_cq_in` input buffer using `k […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 1): The response completely misses the actual vulnerability (CWE-401 memory leak). When mlx5_vector2eqn() fails, the code jumps to err_cqwq without freeing the 'in' buffer that was allocated by kvzalloc. The response explicitly lists 'Memory safety' as not an issue and even notes the error handling path but fails to recogn […]

- *actionability* (score 1): The response concludes the code is safe and provides no remediation guidance. Since the code is actually vulnerable, this is a critical failure in actionability — a developer reading this would take no action on a real memory leak vulnerability.


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


### Case: Qwen3-30B-A3B · instruct · FP · entry_id=273880

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-787']  

**CVE description**: An unauthenticated stack-based buffer overflow vulnerability in common.c's handle_PORT in uftpd FTP server versions 2.10 and earlier can be abused to cause a crash and could potentially lead to remote code execution.  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 3, clarity 5, actionability 4, informativeness 3


**Source code (excerpt)**:

```c
static void handle_PORT(ctrl_t *ctrl, char *str)
{
	int a, b, c, d, e, f;
	char addr[INET_ADDRSTRLEN];
	struct sockaddr_in sin;

	if (ctrl->data_sd > 0) {
		uev_io_stop(&ctrl->data_watcher);
		close(ctrl->data_sd);
		ctrl->data_sd = -1;
	}

	/* Convert PORT command's argument to IP address + port */
	sscanf(str, "%d,%d,%d,%d,%d,%d", &a, &b, &c, &d, &e, &f);
	snprintf(addr, sizeof(addr), "%d.%d.%d.%d", a, b, c, d);

	/* Check IPv4 address using inet_aton(), throw away converted result */
	if (!inet_aton(addr, &(sin.sin_addr))) {
		ERR(0, "Invalid address '%s' given to PORT command", addr);
		send_msg(ctrl->sd, "500 Illegal PORT command.\r\n");
		return;
	}

	strlcpy(ctrl->data_address, addr, sizeof(ctrl->data_address));
	ctrl->data_port = e * 256 + f;

	DBG("Client PORT command accepted for %s:%d", ctrl->data_address, ctrl->data_port);
	send_msg(ctrl->sd, "200 PORT command successful.\r\n");
}
```


**Model response (excerpt)**:

> Let's analyze the provided code step by step to determine whether there is a vulnerability.  ---  ### **1. Context and Purpose** This function `handle_PORT` processes the `PORT` command in an FTP server. The `PORT` command is used to specify the IP address and port number that the client wants the server to use for data connections.  The input `str` is expected to be in the format:   `a,b,c,d,e,f`   where: - `a,b,c,d` form the IP address (e.g., 192,168,1,100) - `e,f` form the port number: `e * 256 + f`  ---  ### **2. Input Parsing** ```c sscanf(str, "%d,%d,%d,%d,%d,%d", &a, &b, &c, &d, &e, &f) […]


**Judge justifications (lowest-scoring dimensions)**:

- *completeness* (score 3): The analysis covers multiple aspects of the code including input parsing, IP validation, and port construction. However, the ground truth indicates this code is safe, and the response incorrectly identifies a vulnerability. While the analysis of missing range validation on e and f is technically accurate as a code qual […]

- *informativeness* (score 3): The analysis provides genuine technical insight about FTP PORT command processing, inet_aton behavior, and snprintf buffer safety. However, it incorrectly classifies the code as vulnerable. The concern about e and f validation is a legitimate code quality observation but is overstated as a security vulnerability — pass […]


**Analyst note**: written confidently and cleanly despite being wrong; still proposes remediation, just for the wrong underlying claim.


---


### Case: Qwen3-30B-A3B · thinking · FP · entry_id=264657

**Ground truth**: safe (model predicted vulnerable)  

**CWE**: ['CWE-416']  

**CVE description**: Use After Free in GitHub repository gpac/gpac prior to v2.1.0-DEV.  

**Plausibility-disconnect score**: +3  

**Judge scores** — completeness 2, clarity 4, actionability 2, informativeness 1


**Source code (excerpt)**:

```c
static GF_Err BM_ParseGlobalQuantizer(GF_BifsDecoder *codec, GF_BitStream *bs, GF_List *com_list)
{
	GF_Node *node;
	GF_Command *com;
	GF_CommandField *inf;
	node = gf_bifs_dec_node(codec, bs, NDT_SFWorldNode);
	if (!node) return GF_NON_COMPLIANT_BITSTREAM;

	/*reset global QP*/
	if (codec->scenegraph->global_qp) {
		gf_node_unregister(codec->scenegraph->global_qp, NULL);
	}
	codec->ActiveQP = NULL;
	codec->scenegraph->global_qp = NULL;

	if (gf_node_get_tag(node) != TAG_MPEG4_QuantizationParameter) {
		//if node was just created (num_instances == 0), unregister
		//otherwise (USE node) don't do anything
		if (!node->sgprivate->num_instances) {
			node->sgprivate->num_instances = 1;
			gf_node_unregister(node, NULL);
		}
		return GF_NON_COMPLIANT_BITSTREAM;
	}

	/*register global QP*/
	codec->ActiveQP = (M_QuantizationParameter *) node;
	codec->ActiveQP->isLocal = 0;
	codec->scenegraph->global_qp = node;

// […]
```


**Model response (excerpt)**:

> We are analyzing the function `BM_ParseGlobalQuantizer` for security vulnerabilities.  Step 1: Analyze the code carefully  The function is part of a BIFS (Binary Format for Scenes) decoder. It processes a global quantizer node.  Key steps: 1. It decodes a node using `gf_bifs_dec_node` and checks if the node is NULL (returns error if so). 2. It checks if there's an existing global quantizer (`codec->scenegraph->global_qp`) and unregisters it (if exists) and resets some state. 3. It checks if the node is of the expected tag (`TAG_MPEG4_QuantizationParameter`). If not, it does:    - If the node w […]


**Judge justifications (lowest-scoring dimensions)**:

- *informativeness* (score 1): The analysis is actively misleading. It misinterprets the reference-counting pattern (register/unregister) as a double-free vulnerability, ignoring the explicit comment explaining the design intent. The fabricated CVE reference (CVE-2019-11250, which is actually a Kubernetes credential leak) further undermines credibil […]

- *completeness* (score 2): The analysis incorrectly identifies a vulnerability in safe code. It focuses on the double gf_node_unregister calls but fails to understand the reference-counting semantics — the comment in the code explicitly states the node is registered twice (once for the command, once for the scenegraph globalQP), so unregistering […]


**Analyst note**: treats one surface concern as the full picture, missing the actual mechanism; substance is thin (recommendation rather than analysis); written confidently and cleanly despite being wrong.


---
