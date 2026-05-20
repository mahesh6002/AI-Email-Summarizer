"use client";

import { useState } from "react";
import { Sparkles, Mail, CheckCircle, Calendar, AlertCircle, Loader2, ArrowRight, Copy, Send, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";

interface SummaryResult {
  summary: string | null;
  action_items: string[];
  deadlines: string | null;
  priority: "High" | "Medium" | "Low" | null;
  generated_reply: string | null;
  processing_time_ms: number;
}

function ResultCard({ result, isVisible }: { result: SummaryResult; isVisible: boolean }) {
  const [copied, setCopied] = useState(false);
  const [replyCopied, setReplyCopied] = useState(false);

  const copyToClipboard = async (text: string, setFunc: (v: boolean) => void) => {
    await navigator.clipboard.writeText(text);
    setFunc(true);
    setTimeout(() => setFunc(false), 2000);
  };

  const getPriorityVariant = (priority: string | null) => {
    switch (priority) {
      case "High":
        return "high";
      case "Medium":
        return "medium";
      case "Low":
        return "low";
      default:
        return "secondary";
    }
  };

  if (!isVisible) return null;

  return (
    <Card className="mt-6 animate-fade-in border-2 border-primary/10 shadow-xl">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Summary Results
            </CardTitle>
            <CardDescription>
              Processed in {result.processing_time_ms}ms
            </CardDescription>
          </div>
          <Button variant="outline" size="sm" onClick={() => copyToClipboard(
            `Summary: ${result.summary}\n\nAction Items: ${result.action_items.join(", ")}\n\nDeadlines: ${result.deadlines || "None"}\n\nPriority: ${result.priority}\n\nReply: ${result.generated_reply || "N/A"}`,
            setCopied
          )} className="gap-2">
            {copied ? <CheckCircle className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            {copied ? "Copied!" : "Copy All"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Priority Badge */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-muted-foreground">Priority:</span>
          <Badge variant={getPriorityVariant(result.priority)} className="text-sm px-3 py-1">
            {result.priority || "Unknown"}
          </Badge>
        </div>

        {/* Summary */}
        <div className="space-y-2">
          <h4 className="font-semibold flex items-center gap-2">
            <Mail className="h-4 w-4" />
            Summary
          </h4>
          <p className="text-sm leading-relaxed text-muted-foreground bg-muted/30 rounded-lg p-4">
            {result.summary || "No summary available"}
          </p>
        </div>

        {/* Action Items */}
        <div className="space-y-2">
          <h4 className="font-semibold flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Action Items
          </h4>
          {result.action_items && result.action_items.length > 0 ? (
            <ul className="space-y-2">
              {result.action_items.map((item, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-sm bg-muted/30 rounded-lg p-3 animate-slide-in"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                    {index + 1}
                  </span>
                  <span className="text-muted-foreground">{item}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground italic">No action items identified</p>
          )}
        </div>

        {/* Deadlines */}
        <div className="space-y-2">
          <h4 className="font-semibold flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Deadlines
          </h4>
          {result.deadlines ? (
            <div className="flex items-center gap-2 text-sm bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400 rounded-lg p-3">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {result.deadlines}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground italic">No deadlines mentioned</p>
          )}
        </div>

        {/* Generated Reply */}
        {result.generated_reply && (
          <div className="space-y-2">
            <h4 className="font-semibold flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Professional Reply Draft
            </h4>
            <div className="relative group">
              <div className="text-sm leading-relaxed text-muted-foreground bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 rounded-lg p-4 border border-blue-100 dark:border-blue-900">
                {result.generated_reply}
              </div>
              <Button
                variant="secondary"
                size="sm"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity gap-1"
                onClick={() => copyToClipboard(result.generated_reply || "", setReplyCopied)}
              >
                {replyCopied ? <CheckCircle className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {replyCopied ? "Copied" : "Copy"}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function Home() {
  const [emailText, setEmailText] = useState("");
  const [generateReply, setGenerateReply] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SummaryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSummarize = async () => {
    if (!emailText.trim()) {
      setError("Please enter email text to summarize");
      return;
    }

    if (emailText.length < 10) {
      setError("Email text is too short. Please provide more context.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("http://localhost:8000/summarize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email_text: emailText,
          source: "manual",
          generate_reply: generateReply,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to summarize email");
      }

      const data: SummaryResult = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const clearAll = () => {
    setEmailText("");
    setResult(null);
    setError(null);
  };

  return (
    <main className="min-h-screen py-12 px-4">
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-primary/60 shadow-lg mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            AI Email Summarizer
          </h1>
          <p className="text-lg text-muted-foreground max-w-xl mx-auto">
            Transform lengthy email threads into concise, actionable summaries with AI-powered insights and professional reply drafts.
          </p>
        </div>

        {/* Input Card */}
        <Card className="border-2 border-border/50 shadow-lg">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Paste Email Content
            </CardTitle>
            <CardDescription>
              Enter the email text you want to summarize (max 20,000 characters)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Paste your email thread here..."
              value={emailText}
              onChange={(e) => setEmailText(e.target.value)}
              className="min-h-[250px] text-base"
              disabled={isLoading}
            />
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {emailText.length.toLocaleString()} / 20,000 characters
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={clearAll} disabled={isLoading}>
                  Clear
                </Button>
              </div>
            </div>

            {/* Generate Reply Toggle */}
            <div className="flex items-center gap-3 p-4 bg-muted/30 rounded-lg">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Generate Professional Reply</span>
              </div>
              <label className="relative inline-flex items-center cursor-pointer ml-auto">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={generateReply}
                  onChange={(e) => setGenerateReply(e.target.checked)}
                  disabled={isLoading}
                />
                <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
              </label>
            </div>

            <Button onClick={handleSummarize} disabled={isLoading || !emailText.trim()} className="w-full gap-2 text-base py-6">
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Summarizing{generateReply ? " & Generating Reply" : ""}...
                </>
              ) : (
                <>
                  <Send className="h-5 w-5" />
                  Summarize Email
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="border-destructive/50 bg-destructive/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-5 w-5" />
                <p className="font-medium">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results */}
        <ResultCard result={result!} isVisible={!!result} />
      </div>
    </main>
  );
}