package org.healthnlp.annotation.labelstudio.result;

import org.healthnlp.annotation.labelstudio.result.value.ChoicesValue;
import org.healthnlp.annotation.labelstudio.result.value.TextAreaValue;

import java.util.List;

public class ChoicesResult extends Result {
    public ChoicesResult(int start, int end, String text, List<String> choices){
        this("DocTimeRel", "text", "manual", start, end, text, choices);
    }


    public ChoicesResult(String from_name, String to_name, String origin, int start, int end, String text, List<String> choices){
        this.from_name = from_name;
        this.to_name = to_name;
        this.origin = origin;
        this.type = "choices";
        this.value = new ChoicesValue(start, end, text, choices);
    }
}
