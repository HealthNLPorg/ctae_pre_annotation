package org.healthnlp.annotation.labelstudio.result.value;

import java.util.List;

public class ChoicesValue extends Value {
    public String text;
    public List<String> choices;

    public ChoicesValue(int start, int end, String text, List<String> choices) {
        super(start, end);
        this.text = text;
        this.choices = choices;
    }
}
