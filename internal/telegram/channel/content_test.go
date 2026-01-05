package channel

import (
	"strings"
	"testing"
)

func TestCleanContent(t *testing.T) {
	tests := []struct {
		name        string
		input       string
		contains    []string
		notContains []string
	}{
		{
			name:        "remove unsupported media message",
			input:       `<div class="message_media_not_supported"><div class="message_media_not_supported_label">Please open Telegram</div></div>Some text`,
			contains:    []string{"Some text"},
			notContains: []string{"message_media_not_supported", "Please open Telegram"},
		},
		{
			name:        "unescape HTML entities",
			input:       `<div>&lt;div&gt;Test&lt;/div&gt; &amp; &quot;quotes&quot;</div>`,
			contains:    []string{"<div>Test</div>", "&", "\"quotes\""},
			notContains: []string{},
		},
		{
			name:        "remove img tags",
			input:       `<div>Text <img src="https://example.com/image.jpg"/> more text</div>`,
			contains:    []string{"Text", "more text"},
			notContains: []string{"<img", "image.jpg"},
		},
		{
			name:        "convert br tags to newlines",
			input:       `<div>First<br/>Second<br>Third</div>`,
			contains:    []string{"First", "Second", "Third"},
			notContains: []string{"<br"},
		},
		{
			name:        "remove link tags",
			input:       `<div>Check <a href="https://example.com">this link</a> here</div>`,
			contains:    []string{"Check", "this link", "here"},
			notContains: []string{"<a", "href"},
		},
		{
			name:        "normalize whitespace",
			input:       `<div>Text   with    multiple     spaces</div>`,
			contains:    []string{"Text with multiple spaces"},
			notContains: []string{},
		},
		{
			name:        "full example with emoji",
			input:       `<div class="message_media_not_supported">Unsupported</div><tg-emoji><i class="emoji"><b>🤌</b></i></tg-emoji><b>Test</b> &amp; <img src="test.jpg"/>`,
			contains:    []string{"🤌", "Test", "&"},
			notContains: []string{"message_media_not_supported", "Unsupported", "<b>", "<img"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := cleanContent(tt.input)

			for _, str := range tt.contains {
				if !strings.Contains(result, str) {
					t.Errorf("expected result to contain %q, but got: %q", str, result)
				}
			}

			for _, str := range tt.notContains {
				if strings.Contains(result, str) {
					t.Errorf("expected result to NOT contain %q, but got: %q", str, result)
				}
			}
		})
	}
}

func TestRealWorldExample(t *testing.T) {
	// Real example from the user's input
	htmlContent := `<div class="message_media_not_supported"><div class="message_media_not_supported_label">Please open Telegram to view this post</div><a href="https://t.me/mediarzn/7051?single" class="message_media_view_in_telegram">VIEW IN TELEGRAM</a></div> <a href="https://t.me/mediarzn/7051?single"><img src="https://cdn4.telesco.pe/file/tXdj9ramslbrhOJ3NvwMI-vgmi1oNes3n3q3VxaokLgyhDwsZD_TZtRgyoCG0UYBMkPm9nSDTrGtG6Z-V9N3JENvwCcCSBK7lfx7VqghQiNBGEVFAfaOCxSFGQGcwTByptkEubtgedfRZMzRfdbNSxFc3DoDdzs0IqHr7UeQ1Xpmfh_B9N2WeVgrkBOhabY7_XkqUle83sB5enKdKRr1n6yDj0Crkr28ZYrgB-cV78IIKpqk94fUv9lT4VjOcHPwz1LcfpkWWACxRhRK35VmBK8RaN05_AqM2jn4-hD4kh4fECfNznaRkwdZ7W30GrDDD1WlMo9MDcHNdZv3TcD-dg.jpg"/></a><br><a href="https://t.me/mediarzn/7052?single"><img src="https://cdn4.telesco.pe/file/VmKn6JJrEArmRLdLdBFN-wEt0Z36VR5tWU2dkRw_xJPASgZU3XsYwJFtR1QQFT87mI77IXaSLmM8LD1enUgOgW1jGX_SZ5VbRd9_0lKf8Up9Wh0TuDLvOlLUeiTJgO4gvsxiULBo9q4jT9LUq0lDBpln87Qlnk8cxe_dw3fm_jH71v-bZBS0f0zqt2a5Nt7qEdG1AmvhOMsKnvWE7p-Su5BjRaQq6nCd6mMzDChp68uSZkmRMfbtAjUGPO7SD8entT6ynJYClOr2laALIfILaQY32EO-0UZdc7J_FnGrCX0-DL6M96rXg5A76-jh6gkVEKRR7xkETSrp6IJxPwdWrA.jpg"/></a><br><div class="tgme_widget_message_text js-message_text" dir="auto"><b>Бонджорно, читатели&amp;&#33;<br/></b><br/>Это мы сходили на выставку Viva l&amp;#39;Italia в художественный музей.</div>`

	content := cleanContent(htmlContent)

	// Content should not contain HTML
	if strings.Contains(content, "<") || strings.Contains(content, ">") {
		t.Errorf("content contains HTML tags: %s", content)
	}

	// Content should contain the Russian text
	if !strings.Contains(content, "Бонджорно") {
		t.Errorf("content should contain Russian text")
	}

	// Content should not contain "message_media_not_supported"
	if strings.Contains(content, "message_media_not_supported") {
		t.Errorf("content should not contain unsupported media message")
	}

	// Content should not contain the unescaped message
	if strings.Contains(content, "Please open Telegram") {
		t.Errorf("content should not contain unsupported media message text")
	}
}
