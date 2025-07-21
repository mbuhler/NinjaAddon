// BacktestMonitorV2.cs
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using NinjaTrader.Gui.AddOns;
using NinjaTrader.Core.Globals;
using NinjaTrader.Data;
using System.Linq;
using StackExchange.Redis;
using Newtonsoft.Json;
#endregion

namespace NinjaTrader.Gui.AddOns
{
    public class BacktestMonitorV2 : AddOnBase
    {
        private List<string> selectedInstruments = new List<string>();
        private ListBox instrumentListBox;
        private TextBox instrumentInput;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "Backtest Monitor V2";
                selectedInstruments = new List<string> { "ES ##-##", "NQ ##-##", "GC ##-##" };
            }
            else if (State == State.Configure)
            {
                if (AddOnState.CustomProperties.ContainsKey("SelectedInstruments"))
                {
                    selectedInstruments = ((string)AddOnState.CustomProperties["SelectedInstruments"])
                        .Split(',').ToList();
                }
            }
        }

        private Expander approvalExpander;
        private TextBlock suggestionText;
        private bool enableHumanApproval = true;

        [NinjaScriptProperty]
        [Display(Name="Enable Human Approval", Order=1, GroupName="Parameters")]
        public bool EnableHumanApproval
        {
            get { return enableHumanApproval; }
            set { enableHumanApproval = value; }
        }

        protected override void OnWindowCreated(Control aControl)
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition());
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(1, GridUnitType.Auto) });
            grid.RowDefinitions.Add(new RowDefinition());
            grid.RowDefinitions.Add(new RowDefinition() { Height = new GridLength(1, GridUnitType.Auto) });

            var topPanel = new StackPanel { Orientation = Orientation.Horizontal };
            instrumentInput = new TextBox { Width = 100 };
            var addButton = new Button { Content = "Add" };
            addButton.Click += AddInstrument_Click;
            var removeButton = new Button { Content = "Remove Selected" };
            removeButton.Click += RemoveInstrument_Click;
            topPanel.Children.Add(instrumentInput);
            topPanel.Children.Add(addButton);
            topPanel.Children.Add(removeButton);

            instrumentListBox = new ListBox();
            UpdateInstrumentList();

            approvalExpander = new Expander
            {
                Header = "AI Suggestions",
                IsExpanded = false,
                Visibility = Visibility.Collapsed
            };
            var approvalPanel = new StackPanel();
            suggestionText = new TextBlock { TextWrapping = TextWrapping.Wrap };
            var approveButton = new Button { Content = "Approve" };
            approveButton.Click += Approve_Click;
            var rejectButton = new Button { Content = "Reject" };
            rejectButton.Click += Reject_Click;
            approvalPanel.Children.Add(suggestionText);
            approvalPanel.Children.Add(approveButton);
            approvalPanel.Children.Add(rejectButton);
        }

        private void Approve_Click(object sender, RoutedEventArgs e)
        {
        }

        private void CheckForSuggestions()
        {
            try
            {
                string filePath = NinjaTrader.Core.Globals.UserDataDir + "output/analysis_response.json";
                if (System.IO.File.Exists(filePath))
                {
                    string json = System.IO.File.ReadAllText(filePath);
                    if (EnableHumanApproval)
                    {
                        suggestionText.Text = json;
                        approvalExpander.Visibility = Visibility.Visible;
                        approvalExpander.IsExpanded = true;
                    }
                    else
                    {
                        // Auto-approve
                        Log("Auto-approving suggestion.", LogLevel.Info);
                        // Apply the suggestion to the strategy here.
                    }
                }
            }
            catch (Exception e)
            {
                Log($"Error checking for suggestions: {e.Message}", LogLevel.Error);
            }
        }

        private void Approve_Click(object sender, RoutedEventArgs e)
        {
            Log("Suggestion approved.", LogLevel.Info);
            // Apply the suggestion to the strategy here.
            approvalExpander.Visibility = Visibility.Collapsed;
        }

        private void Reject_Click(object sender, RoutedEventArgs e)
        {
            Log("Suggestion rejected.", LogLevel.Info);
            approvalExpander.Visibility = Visibility.Collapsed;
        }
            approvalExpander.Content = approvalPanel;

            grid.Children.Add(topPanel);
            Grid.SetRow(instrumentListBox, 1);
            grid.Children.Add(instrumentListBox);
            Grid.SetRow(approvalExpander, 2);
            grid.Children.Add(approvalExpander);

            aControl.Content = grid;
        }

        private void AddInstrument_Click(object sender, RoutedEventArgs e)
        {
            string newInstrument = instrumentInput.Text.Trim();
            if (!string.IsNullOrEmpty(newInstrument) && !selectedInstruments.Contains(newInstrument))
            {
                selectedInstruments.Add(newInstrument);
                UpdateInstrumentList();
                StartStreaming(newInstrument);
            }
        }

        private void RemoveInstrument_Click(object sender, RoutedEventArgs e)
        {
            if (instrumentListBox.SelectedItem != null)
            {
                string instrumentToRemove = (string)instrumentListBox.SelectedItem;
                selectedInstruments.Remove(instrumentToRemove);
                UpdateInstrumentList();
                StopStreaming(instrumentToRemove);
            }
        }

        private void UpdateInstrumentList()
        {
            instrumentListBox.ItemsSource = null;
            instrumentListBox.ItemsSource = selectedInstruments;
            AddOnState.CustomProperties["SelectedInstruments"] = string.Join(",", selectedInstruments);
        }

        private ConnectionMultiplexer redis;
        private IDatabase db;

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Name = "Backtest Monitor V2";
                selectedInstruments = new List<string> { "ES ##-##", "NQ ##-##", "GC ##-##" };
            }
            else if (State == State.Configure)
            {
                if (AddOnState.CustomProperties.ContainsKey("SelectedInstruments"))
                {
                    selectedInstruments = ((string)AddOnState.CustomProperties["SelectedInstruments"])
                        .Split(',').ToList();
                }
                try
                {
                    redis = ConnectionMultiplexer.Connect("localhost");
                    db = redis.GetDatabase();
                    Log("Connected to Redis.", LogLevel.Info);
                }
                catch (Exception e)
                {
                    Log($"Error connecting to Redis: {e.Message}", LogLevel.Error);
                }
            }
        }

        private void StartStreaming(string instrument)
        {
            // In a real implementation, we would use AddOnMarketData or BarsRequest here.
            // For now, we will just log that we are starting to stream.
            Log($"Starting to stream {instrument}", LogLevel.Info);
            // This is a placeholder for the actual market data subscription
            // OnMarketData(instrument, new MarketDataEventArgs());
        }

        private void OnMarketData(string instrument, MarketDataEventArgs args)
        {
            if (db == null) return;

            var tick = new
            {
                instrument = instrument,
                timestamp = DateTime.UtcNow.ToString("o"),
                lastPrice = args.Price,
                bid = args.Bid,
                ask = args.Ask,
                volume = args.Volume
            };

            string json = JsonConvert.SerializeObject(tick);
            string key = $"tickstream:{instrument}";

            db.ListLeftPushAsync(key, json);
            db.ListTrimAsync(key, 0, 999);
        }

        private void StopStreaming(string instrument)
        {
            Log($"Stopping to stream {instrument}", LogLevel.Info);
        }

        protected override void OnTermination()
        {
            foreach(var instrument in selectedInstruments)
            {
                StopStreaming(instrument);
            }
        }
    }
}
