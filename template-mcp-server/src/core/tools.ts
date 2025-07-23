import { FastMCP } from "fastmcp";
import { z } from "zod";
import * as services from "./services/index.js";

/**
 * Register all tools with the MCP server
 * 
 * @param server The FastMCP server instance
 */
export function registerTools(server: FastMCP) {
  // Greeting tool
  server.addTool({
    name: "hello_world",
    description: "A simple hello world tool",
    parameters: z.object({
      name: z.string().describe("Name to greet")
    }),
    execute: async (params) => {
      const greeting = services.GreetingService.generateGreeting(params.name);
      return greeting;
    }
  });

  // Farewell tool
  server.addTool({
    name: "goodbye",
    description: "A simple goodbye tool",
    parameters: z.object({
      name: z.string().describe("Name to bid farewell to")
    }),
    execute: async (params) => {
      const farewell = services.GreetingService.generateFarewell(params.name);
      return farewell;
    }
  });

  // Get financial data tool
  server.addTool({
    name: "get_financial_data",
    description: "Gets financial data",
    parameters: z.object({}),
    execute: async () => {
      const response = await fetch("https://n8n.tuongeechat.com/webhook/5f7df1a1-054c-42d3-8f84-89045ae34dba");
      const data = await response.json();

      // Filter and clean records (remove rows with no month or profit is a month string)
      const rows = data.filter((row: any) => row.MONTH && !isNaN(Number(row.SALES)));

      // Format the first few months
      const summary = rows.map((row: any) => {
        return `📅 **${row.MONTH}**\n- Sales: KSH ${row.SALES.toLocaleString()}\n- Spend: KSH ${row.SPEND.toLocaleString()}\n- Profit: KSH ${row.PROFIT.toLocaleString()}\n- Gross Margin: KSH ${row["Gross Margin"].toLocaleString()}\n- Bills: KSH ${row.bills?.toLocaleString() || '0'}\n- Rent: KSH ${row.rent?.toLocaleString() || '0'}\n- Groceries: KSH ${row.groceries?.toLocaleString() || '0'}\n`;
      }).join('\n\n');

      return {
        content: [
          {
            type: "text",
            text: `Here’s a summary of recent monthly financials:\n\n${summary}`
          }
        ]
      };
    }
  });

  // Get bills data tool
  server.addTool({
    name: "get_bills_data",
    description: "Gets bills data",
    parameters: z.object({}),
    execute: async () => {
      const response = await fetch("https://n8n.tuongeechat.com/webhook/73ab8574-6a42-49d4-ae71-c65138680699");
      const data = await response.json();

      return {
        content: [
          {
            type: "text",
            text: data.data  // Access the string inside { data: "..." }
          }
        ]
      };
    }
  });

  // Activate a customer account
  server.addTool({
    name: "activate_account",
    description: "Activates a customer's account by email",
    parameters: z.object({
      email: z.string().email().describe("Customer email to activate")
    }),
    execute: async ({ email }) => {
      const url = `https://expatelitesingles.com/api/sirri_api/activate/${email}`;
      const response = await fetch(url, { method: "GET" });
      const data = await response.json();

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data)
          }
        ]
      };
    }
  });

  // Delegate automatic messaging tasks
  server.addTool({
    name: "delegate_auto_messages",
    description: "Delegates messaging tasks for a user by email",
    parameters: z.object({
      email: z.string().email().describe("Customer email for scheduling messages")
    }),
    execute: async ({ email }) => {
      const response = await fetch(
        "https://expatelitesingles.com/api/sirri_api/auto_messages_email",
        {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: `EMAIL=`+email
        }
      );
      const data = await response.json();

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data)
          }
        ]
      };
    }
  });

  // Check if a user has uploaded a profile picture
  server.addTool({
    name: "has_profile_picture",
    description: "Checks whether the specified user has a profile picture",
    parameters: z.object({
      email: z.string().email().describe("Customer email")
    }),
    execute: async ({ email }) => {
      const url = `https://expatelitesingles.com/api/has_picture?EMAIL=${email}`;
      const response = await fetch(url);
      const data = await response.json();

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(data)
          }
        ]
      };
    }
  });
}
