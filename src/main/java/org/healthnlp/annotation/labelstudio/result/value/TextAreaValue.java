package org.healthnlp.annotation.labelstudio.result.value;

import java.util.List;

public class TextAreaValue extends Value {
    public List<String> text;

    public TextAreaValue(int start, int end, List<String> text) {
        super(start, end);
        this.text = text;
    }
}
