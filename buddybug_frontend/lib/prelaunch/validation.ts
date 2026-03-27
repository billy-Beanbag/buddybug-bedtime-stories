import { z } from "zod";

export const signupSchema = z.object({
  parentEmail: z.string().trim().email("Enter a valid email address."),
  childFirstName: z
    .string()
    .trim()
    .min(1, "Enter your child's first name.")
    .max(40, "Keep the name under 40 characters."),
  childAge: z.coerce.number().int().min(2, "Age must be at least 2.").max(12, "Age must be 12 or younger."),
  consentToEmails: z.boolean().refine((value) => value === true, {
    message: "Please confirm that we can send weekly bedtime stories by email.",
  }),
  marketingAttribution: z.string().trim().max(120).optional().nullable(),
  website: z.string().max(0).optional().default(""),
});

export const unsubscribeSchema = z.object({
  token: z.string().trim().min(24, "Missing unsubscribe token."),
});

export type SignupInput = z.infer<typeof signupSchema>;
