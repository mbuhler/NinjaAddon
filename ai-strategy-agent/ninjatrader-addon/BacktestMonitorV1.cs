#region Using declarations
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Media; // For SystemSounds
using System.Text; // For StringBuilder
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using Microsoft.CSharp.RuntimeBinder; // For catching dynamic property errors
using Microsoft.Win32;
using NinjaTrader.Cbi;
using NinjaTrader.Code;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.Gui.Tools;
using NinjaTrader.NinjaScript.AddOns;
using NinjaTrader.NinjaScript.DrawingTools;
using NinjaTrader.NinjaScript.Strategies;
using System.Web.Script.Serialization; // For JSON Save/Load
#endregion

namespace NinjaTrader.NinjaScript.AddOns
{
	public class BacktestMonitorV1 : AddOnBase
	{
		private NTMenuItem            monitorMenuItem;
		private BacktestMonitorWindow monitorWindow;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Name = "Backtest Monitor V1";
			}
		}

		protected override void OnWindowCreated(Window window)
		{
			if (!(window is ControlCenter cc))
				return;

			monitorMenuItem = new NTMenuItem { Header = "Backtest Monitor V1" };
			monitorMenuItem.Click += (s, e) => ShowWindow();

			var toolsMenu = cc.FindFirst("ControlCenterMenuItemTools") as NTMenuItem;
			if (toolsMenu != null)
				toolsMenu.Items.Add(monitorMenuItem);
		}

		protected override void OnWindowDestroyed(Window window)
		{
			if (monitorMenuItem != null && window is ControlCenter cc)
			{
				var toolsMenu = cc.FindFirst("ControlCenterMenuItemTools") as NTMenuItem;
				if (toolsMenu != null)
					toolsMenu.Items.Remove(monitorMenuItem);
			}

			if (monitorWindow != null)
			{
				monitorWindow.Close();
				monitorWindow = null;
			}
		}

		private void ShowWindow()
		{
			if (monitorWindow == null || PresentationSource.FromVisual(monitorWindow) == null)
			{
				monitorWindow = new BacktestMonitorWindow();
				monitorWindow.Show();
			}
			else
			{
				monitorWindow.Activate();
			}
		}
	}

	public enum StrategyStatus { Running, Paused, MissingData, Unknown }

	public class BacktestMonitorWindow : NTWindow
	{
		private ObservableCollection<RunningStrategyInfo> runningStrategies = new ObservableCollection<RunningStrategyInfo>();
		private ObservableCollection<ComparisonResult> comparisonResults = new ObservableCollection<ComparisonResult>();
		private List<DriftEvent> driftEvents = new List<DriftEvent>();
		private DataGrid strategyMonitorGrid, comparisonGrid;
		private TextBlock dateRangeLabel, llmStatusText;
		private ComboBox providerComboBox, modelComboBox;
		private PasswordBox apiKeyBox;
		private TextBox chatInputBox;
		private TextBlock chatLogText;
		private CheckBox autoPauseCheckBox, manualRestartCheckBox;
		private readonly string logDirectory = Path.Combine(NinjaTrader.Core.Globals.UserDataDir, "BacktestMonitorLogs");
		private MonitorSettings monitorSettings = new MonitorSettings();
		private LlmConfig llmConfig = new LlmConfig();
		private static readonly HttpClient httpClient = new HttpClient();
		private List<ChatMessage> chatHistory = new List<ChatMessage>();
		private DateTime? analysisStartDate, analysisEndDate;
		private DispatcherTimer _monitorTimer;
		private TextBlock summaryAtRiskText, summaryLivePfText, summaryBacktestPfText, summaryPnlDeltaText;

		public BacktestMonitorWindow()
		{
			Caption = "Backtest Monitor v2.5 - Final";
			Width = 2000; Height = 900;
			WindowStartupLocation = WindowStartupLocation.Manual;
			Left = SystemParameters.WorkArea.Left + 100;
			Top = SystemParameters.WorkArea.Top + 100;
			Content = BuildUI();
			Directory.CreateDirectory(logDirectory);
			LoadAllConfigs();
			LoadChatHistory();
			Closing += (s, e) => { SaveAllConfigs(); SaveChatHistory(); _monitorTimer.Stop(); };
			PopulateRunningStrategies();

			_monitorTimer = new DispatcherTimer();
			_monitorTimer.Interval = TimeSpan.FromMinutes(1);
			_monitorTimer.Tick += StartMonitoringLoop;
			_monitorTimer.Start();
		}

		#region UI Construction
		private UIElement BuildUI()
		{
			var mainTabs = new TabControl { Padding = new Thickness(5) };
			mainTabs.Items.Add(new TabItem { Header = "Strategy Monitor", Content = BuildStrategyMonitorTab() });
			mainTabs.Items.Add(new TabItem { Header = "Comparison View", Content = BuildComparisonTab() });
			mainTabs.Items.Add(new TabItem { Header = "AI Diagnostics", Content = BuildLlmAnalystPanel() });
			mainTabs.Items.Add(new TabItem { Header = "Settings", Content = BuildSettingsTab() });
			return mainTabs;
		}

		private UIElement BuildStrategyMonitorTab()
		{
			var monitorGridPanel = new Grid();
			monitorGridPanel.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
			monitorGridPanel.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
			var refreshButton = new Button { Content = "Refresh Running Strategies", Margin = new Thickness(5), Padding = new Thickness(5), HorizontalAlignment = HorizontalAlignment.Left };
			refreshButton.Click += (s, e) => PopulateRunningStrategies();
			Grid.SetRow(refreshButton, 0);
			monitorGridPanel.Children.Add(refreshButton);
			strategyMonitorGrid = new DataGrid { Margin = new Thickness(5,0,5,5), AutoGenerateColumns = false, IsReadOnly = true };
			
			var rowStyle = new Style(typeof(DataGridRow));
			var runningTrigger = new DataTrigger { Binding = new Binding("Status"), Value = StrategyStatus.Running };
			runningTrigger.Setters.Add(new Setter(BackgroundProperty, Brushes.LightGreen));
			var pausedByDriftTrigger = new DataTrigger { Binding = new Binding("PausedByDrift"), Value = true };
			pausedByDriftTrigger.Setters.Add(new Setter(BackgroundProperty, Brushes.LightYellow));
			var missingDataTrigger = new DataTrigger { Binding = new Binding("Status"), Value = StrategyStatus.MissingData };
			missingDataTrigger.Setters.Add(new Setter(BackgroundProperty, Brushes.LightCoral));
			rowStyle.Triggers.Add(runningTrigger);
			rowStyle.Triggers.Add(pausedByDriftTrigger);
			rowStyle.Triggers.Add(missingDataTrigger);
			strategyMonitorGrid.RowStyle = rowStyle;

			strategyMonitorGrid.Columns.Add(new DataGridTextColumn { Header = "Strategy Name", Binding = new Binding("Name"), FontWeight = FontWeights.Bold, Width = new DataGridLength(1, DataGridLengthUnitType.Star) });
			strategyMonitorGrid.Columns.Add(new DataGridTextColumn { Header = "Instrument", Binding = new Binding("Instrument"), Width = new DataGridLength(1, DataGridLengthUnitType.Auto) });
			strategyMonitorGrid.Columns.Add(new DataGridTextColumn { Header = "Account", Binding = new Binding("Account"), Width = new DataGridLength(1, DataGridLengthUnitType.Auto) });
			strategyMonitorGrid.Columns.Add(new DataGridTextColumn { Header = "Status", Binding = new Binding("Status"), Width = new DataGridLength(1, DataGridLengthUnitType.Auto) });
			strategyMonitorGrid.Columns.Add(CreateButtonColumn("Backtest", "LoadBacktest_Click", "IsBacktestLoaded", Brushes.LightCoral, Brushes.LightGreen));
			strategyMonitorGrid.Columns.Add(CreateButtonColumn("Live", "LoadLive_Click", "IsLiveLoaded", Brushes.LightCoral, Brushes.LightGreen));
			strategyMonitorGrid.Columns.Add(CreateButtonColumn("Pause", "PauseStrategy_Click", "CanPause", Brushes.Orange, Brushes.Gray));
			strategyMonitorGrid.Columns.Add(CreateButtonColumn("Restart", "RestartStrategy_Click", "CanRestart", Brushes.LightBlue, Brushes.Gray));
			strategyMonitorGrid.Columns.Add(CreateButtonColumn("Reset Drift", "ResetDrift_Click", "CanResetDrift", Brushes.Gray, Brushes.MediumSeaGreen));
			strategyMonitorGrid.ItemsSource = runningStrategies;
			Grid.SetRow(strategyMonitorGrid, 1);
			monitorGridPanel.Children.Add(strategyMonitorGrid);
			return monitorGridPanel;
		}

		private UIElement BuildComparisonTab()
		{
			var mainPanel = new Grid();
			mainPanel.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
			mainPanel.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
			mainPanel.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

			var summaryPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(10, 5, 5, 10) };
			summaryAtRiskText = new TextBlock { FontWeight = FontWeights.Bold, Margin = new Thickness(0,0,20,0) };
			summaryLivePfText = new TextBlock { Margin = new Thickness(0,0,20,0) };
			summaryBacktestPfText = new TextBlock { Margin = new Thickness(0,0,20,0) };
			summaryPnlDeltaText = new TextBlock { Margin = new Thickness(0,0,20,0) };
			summaryPanel.Children.Add(summaryAtRiskText);
			summaryPanel.Children.Add(summaryLivePfText);
			summaryPanel.Children.Add(summaryBacktestPfText);
			summaryPanel.Children.Add(summaryPnlDeltaText);
			Grid.SetRow(summaryPanel, 0);
			mainPanel.Children.Add(summaryPanel);

			comparisonGrid = new DataGrid { Margin = new Thickness(5), IsReadOnly = true, AutoGenerateColumns = false, CanUserAddRows = false, CanUserDeleteRows = false, FrozenColumnCount = 2 };
			comparisonGrid.MouseDoubleClick += ComparisonGrid_MouseDoubleClick;
			var rowStyle = new Style(typeof(DataGridRow));
			var atRiskTrigger = new DataTrigger { Binding = new Binding("IsAtRisk"), Value = true };
			atRiskTrigger.Setters.Add(new Setter(BackgroundProperty, Brushes.MistyRose));
			atRiskTrigger.Setters.Add(new Setter(ForegroundProperty, Brushes.DarkRed));
			rowStyle.Triggers.Add(atRiskTrigger);
			comparisonGrid.RowStyle = rowStyle;
			comparisonGrid.Columns.Add(new DataGridTextColumn { Header = "Strategy", Binding = new Binding("StrategyName"), FontWeight = FontWeights.Bold, IsReadOnly = true });
			comparisonGrid.Columns.Add(new DataGridTextColumn { Header = "Symbol", Binding = new Binding("Symbol"), IsReadOnly = true });
			comparisonGrid.Columns.Add(new DataGridTextColumn { Header = "Status", Binding = new Binding("Status"), IsReadOnly = true });
			comparisonGrid.Columns.Add(new DataGridTextColumn { Header = "Live PnL", Binding = new Binding("LiveStats.PnL") { StringFormat = "C" }, IsReadOnly = true });
			comparisonGrid.Columns.Add(new DataGridTextColumn { Header = "Live PF", Binding = new Binding("LiveStats.ProfitFactor") { StringFormat = "F2" }, IsReadOnly = true });
			comparisonGrid.Columns.Add(CreateDeltaColumn("PF Δ", "ProfitFactorDiff", "F2"));
			comparisonGrid.Columns.Add(CreateDeltaColumn("Win Rate Δ", "WinRateDiff", "P1"));
			comparisonGrid.Columns.Add(CreateSlopeColumn("PF Δ Slope", "ProfitFactorSlope", "F3", false, "SlopeHistory"));
			comparisonGrid.Columns.Add(CreateSlopeColumn("Win% Δ Slope", "WinRateSlope", "F3", false, "SlopeHistory"));
			comparisonGrid.Columns.Add(CreateSlopeColumn("DD Δ Slope", "DrawdownSlope", "F1", true, "SlopeHistory"));
			comparisonGrid.ItemsSource = comparisonResults;
			Grid.SetRow(comparisonGrid, 1);
			mainPanel.Children.Add(comparisonGrid);
			
			var bottomPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(5, 10, 5, 5) };
			var exportButton = new Button { Content = "Export Summary", HorizontalAlignment = HorizontalAlignment.Left };
			exportButton.Click += (s, e) => ExportSummary();
			var saveButton = new Button { Content = "Save Comparison State", Margin = new Thickness(10, 0, 5, 0) };
			saveButton.Click += (s, e) => SaveComparisonState();
			var loadButton = new Button { Content = "Load Comparison State", Margin = new Thickness(5, 0, 5, 0) };
			loadButton.Click += (s, e) => LoadComparisonState();
			bottomPanel.Children.Add(exportButton);
			bottomPanel.Children.Add(saveButton);
			bottomPanel.Children.Add(loadButton);
			Grid.SetRow(bottomPanel, 2);
			mainPanel.Children.Add(bottomPanel);
			
			return mainPanel;
		}

		private UIElement BuildLlmAnalystPanel()
		{
			var llmPanel = new StackPanel { Margin = new Thickness(5) };
			llmPanel.Children.Add(BuildLlmConfigPanel());
			var chatBorder = new Border { BorderBrush = Brushes.Gray, BorderThickness = new Thickness(1), Margin = new Thickness(5), Padding = new Thickness(5), MinHeight=300 };
			var chatGrid = new Grid();
			chatGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
			chatGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
			chatLogText = new TextBlock { TextWrapping = TextWrapping.Wrap };
			var chatScrollViewer = new ScrollViewer { Content = chatLogText, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
			chatGrid.Children.Add(chatScrollViewer); Grid.SetRow(chatScrollViewer, 0);
			var inputPanel = new StackPanel { Orientation = Orientation.Vertical, Margin = new Thickness(0, 5, 0, 0) };
			chatInputBox = new TextBox { MinHeight = 60, TextWrapping = TextWrapping.Wrap, AcceptsReturn = true, VerticalScrollBarVisibility = ScrollBarVisibility.Auto };
			chatInputBox.KeyDown += (s, e) => { if (e.Key == Key.Enter && !Keyboard.Modifiers.HasFlag(ModifierKeys.Shift)) { ProcessUserQueryAsync(); e.Handled = true; } };
			var buttonPanel = new StackPanel { Orientation = Orientation.Horizontal, Margin=new Thickness(0,5,0,0) };
			var sendButton = new Button { Content = "Send", Margin = new Thickness(5, 0, 0, 0) }; sendButton.Click += (s, e) => ProcessUserQueryAsync();
			var clearChatButton = new Button { Content = "Clear History", Margin = new Thickness(5, 0, 0, 0) }; clearChatButton.Click += (s, e) => { chatHistory.Clear(); chatLogText.Inlines.Clear(); SaveChatHistory(); };
			buttonPanel.Children.Add(sendButton);
			buttonPanel.Children.Add(clearChatButton);
			inputPanel.Children.Add(chatInputBox);
			inputPanel.Children.Add(buttonPanel);
			chatGrid.Children.Add(inputPanel); Grid.SetRow(inputPanel, 1);
			chatBorder.Child = chatGrid;
			llmPanel.Children.Add(chatBorder);
			return llmPanel;
		}

		private UIElement BuildSettingsTab()
		{
			var settingsPanel = new StackPanel { Margin = new Thickness(20) };
			settingsPanel.Children.Add(new TextBlock { Text = "Drift Management", FontSize = 16, FontWeight = FontWeights.Bold, Margin = new Thickness(0,0,0,10) });
			autoPauseCheckBox = new CheckBox { Content = "Enable Auto-Pause on Drift", Margin = new Thickness(5), IsChecked = monitorSettings.EnableAutoPause };
			manualRestartCheckBox = new CheckBox { Content = "Require Manual Restart After Auto-Pause", Margin = new Thickness(5), IsChecked = monitorSettings.RequireManualRestart };
			settingsPanel.Children.Add(autoPauseCheckBox);
			settingsPanel.Children.Add(manualRestartCheckBox);
			var saveButton = new Button { Content = "Save Settings", Margin = new Thickness(5, 20, 5, 5), Padding = new Thickness(5), HorizontalAlignment = HorizontalAlignment.Left };
			saveButton.Click += (s, e) => SaveAllConfigs();
			settingsPanel.Children.Add(saveButton);
			return settingsPanel;
		}
		#endregion

		#region UI Helpers
		private DataGridTemplateColumn CreateButtonColumn(string header, string clickHandlerName, string bindingPath, Brush falseBrush, Brush trueBrush)
		{
			var column = new DataGridTemplateColumn { Header = header, Width = new DataGridLength(1, DataGridLengthUnitType.Auto) };
			var factory = new FrameworkElementFactory(typeof(Button));
			factory.SetValue(ContentProperty, header);
			factory.AddHandler(Button.ClickEvent, new RoutedEventHandler(OnGridButtonClick));
			factory.SetValue(TagProperty, clickHandlerName); 
			var style = new Style(typeof(Button));
			style.Setters.Add(new Setter(MarginProperty, new Thickness(2)));
			style.Setters.Add(new Setter(PaddingProperty, new Thickness(5,2,5,2)));
			var trueTrigger = new DataTrigger { Binding = new Binding(bindingPath), Value = true };
			trueTrigger.Setters.Add(new Setter(BackgroundProperty, trueBrush));
			trueTrigger.Setters.Add(new Setter(IsEnabledProperty, true));
			style.Triggers.Add(trueTrigger);
			var falseTrigger = new DataTrigger { Binding = new Binding(bindingPath), Value = false };
			falseTrigger.Setters.Add(new Setter(BackgroundProperty, falseBrush));
			falseTrigger.Setters.Add(new Setter(IsEnabledProperty, false));
			style.Triggers.Add(falseTrigger);
			factory.SetValue(StyleProperty, style);
			column.CellTemplate = new DataTemplate { VisualTree = factory };
			return column;
		}

		private void OnGridButtonClick(object sender, RoutedEventArgs e)
		{
			var button = sender as Button;
			if (button == null) return;
			var strategyInfo = button.DataContext as RunningStrategyInfo;
			if (strategyInfo == null) return;
			string handlerName = button.Tag as string;
			switch (handlerName)
			{
				case "LoadBacktest_Click": LoadBacktestForStrategy(strategyInfo); break;
				case "LoadLive_Click": LoadLiveForStrategy(strategyInfo); break;
				case "PauseStrategy_Click": PauseStrategy(strategyInfo); break;
				case "RestartStrategy_Click": RestartStrategy(strategyInfo); break;
				case "ResetDrift_Click": ResetDriftStatus(strategyInfo); break;
			}
		}

		private DataGridTemplateColumn CreateDeltaColumn(string header, string bindingPath, string format, bool invertColors = false)
		{
			var column = new DataGridTemplateColumn { Header = header, IsReadOnly = true };
			var factory = new FrameworkElementFactory(typeof(TextBlock));
			factory.SetBinding(TextBlock.TextProperty, new Binding(bindingPath) { StringFormat = format });
			var style = new Style(typeof(TextBlock));
			style.Setters.Add(new Setter(HorizontalAlignmentProperty, HorizontalAlignment.Right));
			style.Setters.Add(new Setter(PaddingProperty, new Thickness(5)));
			var positiveTrigger = new DataTrigger { Binding = new Binding(bindingPath) { Converter = new GreaterThanConverter(), ConverterParameter = 0.0 }, Value = true };
			positiveTrigger.Setters.Add(new Setter(ForegroundProperty, invertColors ? Brushes.Red : Brushes.Green));
			style.Triggers.Add(positiveTrigger);
			var negativeTrigger = new DataTrigger { Binding = new Binding(bindingPath) { Converter = new LessThanConverter(), ConverterParameter = 0.0 }, Value = true };
			negativeTrigger.Setters.Add(new Setter(ForegroundProperty, invertColors ? Brushes.Green : Brushes.Red));
			style.Triggers.Add(negativeTrigger);
			factory.SetValue(StyleProperty, style);
			column.CellTemplate = new DataTemplate { VisualTree = factory };
			return column;
		}

		private DataGridTemplateColumn CreateSlopeColumn(string header, string bindingPath, string format, bool invertColors = false, string historyBindingPath = null)
		{
			var column = new DataGridTemplateColumn { Header = header, IsReadOnly = true };
			var factory = new FrameworkElementFactory(typeof(TextBlock));
			var textMultiBinding = new MultiBinding { StringFormat = "{0} {1}" };
			textMultiBinding.Bindings.Add(new Binding(bindingPath) { Converter = new SlopeToArrowConverter(), ConverterParameter = invertColors });
			textMultiBinding.Bindings.Add(new Binding(bindingPath) { StringFormat = format });
			factory.SetBinding(TextBlock.TextProperty, textMultiBinding);
			
			if (!string.IsNullOrEmpty(historyBindingPath))
			{
				var tooltipMultiBinding = new MultiBinding { Converter = new HistoryToTrendConverter() };
				tooltipMultiBinding.Bindings.Add(new Binding(bindingPath));
				tooltipMultiBinding.Bindings.Add(new Binding(historyBindingPath));
				tooltipMultiBinding.Bindings.Add(new Binding() { Source = bindingPath });
				factory.SetBinding(ToolTipProperty, tooltipMultiBinding);
			}

			var style = new Style(typeof(TextBlock));
			style.Setters.Add(new Setter(HorizontalAlignmentProperty, HorizontalAlignment.Right));
			style.Setters.Add(new Setter(PaddingProperty, new Thickness(5)));
			var positiveTrigger = new DataTrigger { Binding = new Binding(bindingPath) { Converter = new GreaterThanConverter(), ConverterParameter = 0.0 }, Value = true };
			positiveTrigger.Setters.Add(new Setter(ForegroundProperty, invertColors ? Brushes.Red : Brushes.Green));
			style.Triggers.Add(positiveTrigger);
			var negativeTrigger = new DataTrigger { Binding = new Binding(bindingPath) { Converter = new LessThanConverter(), ConverterParameter = 0.0 }, Value = true };
			negativeTrigger.Setters.Add(new Setter(ForegroundProperty, invertColors ? Brushes.Green : Brushes.Red));
			style.Triggers.Add(negativeTrigger);
			factory.SetValue(StyleProperty, style);
			column.CellTemplate = new DataTemplate { VisualTree = factory };
			return column;
		}
		
		private void ComparisonGrid_MouseDoubleClick(object sender, MouseButtonEventArgs e)
		{
			if (!(comparisonGrid.SelectedItem is ComparisonResult selectedResult)) return;

			var historyWindow = new Window
			{
				Title = $"{selectedResult.StrategyName} - Slope History",
				Width = 400, Height = 600,
				WindowStartupLocation = WindowStartupLocation.CenterOwner,
				Owner = this
			};
			
			var scrollViewer = new ScrollViewer();
			var stackPanel = new StackPanel { Margin = new Thickness(10) };
			
			stackPanel.Children.Add(new TextBlock { Text = "Slope History (Last 20)", FontWeight = FontWeights.Bold, FontSize = 16, Margin = new Thickness(0,0,0,10) });

			var historyText = new StringBuilder();
			foreach(var snapshot in selectedResult.SlopeHistory.Reverse<SlopeSnapshot>())
			{
				historyText.AppendLine($"{snapshot.Timestamp:G}");
				historyText.AppendLine($"  PF Slope: {snapshot.ProfitFactorSlope:F3}");
				historyText.AppendLine($"  Win% Slope: {snapshot.WinRateSlope:F3}");
				historyText.AppendLine($"  DD Slope: {snapshot.DrawdownSlope:F1}");
				historyText.AppendLine();
			}

			stackPanel.Children.Add(new TextBlock { Text = historyText.ToString(), FontFamily = new FontFamily("Courier New") });
			scrollViewer.Content = stackPanel;
			historyWindow.Content = scrollViewer;
			historyWindow.Show();
		}
		#endregion

		#region Core Logic: Strategy Detection and Management
		private void StartMonitoringLoop(object sender, EventArgs e)
		{
			UpdateComparisonView();
		}

		private void PopulateRunningStrategies()
		{
			runningStrategies.Clear();
			
			foreach (Window window in System.Windows.Application.Current.Windows)
			{
				if (window is NinjaTrader.Gui.Chart.Chart chartWindow)
				{
					TabControl chartTabs = chartWindow.FindFirst("ChartTabs") as TabControl;
					if (chartTabs == null) continue;

					foreach (TabItem tab in chartTabs.Items)
					{
						if (tab.Content is ChartControl chartControl)
						{
							foreach (Strategy strategy in chartControl.Strategies)
							{
								if (strategy.State != State.Realtime || strategy.BarsArray.Length == 0)
									continue;
								
								var info = new RunningStrategyInfo
								{
									Name = strategy.Name,
									Instrument = strategy.Instrument.FullName,
									Account = strategy.Account.Name,
									Status = strategy.IsEnabled ? StrategyStatus.Running : StrategyStatus.Paused,
									StrategyInstance = strategy
								};

								string expectedBacktestFile = Path.Combine(logDirectory, $"{info.UniqueId}_Backtest.csv");
								if(File.Exists(expectedBacktestFile))
									AutoLoadBacktestData(info, expectedBacktestFile);

								string expectedLiveFile = Path.Combine(logDirectory, $"{info.UniqueId}_Live.csv");
								if(File.Exists(expectedLiveFile))
									AutoLoadLiveData(info, expectedLiveFile);

								if (!info.IsBacktestLoaded || !info.IsLiveLoaded)
									info.Status = StrategyStatus.MissingData;

								if (!runningStrategies.Any(s => s.UniqueId == info.UniqueId))
									runningStrategies.Add(info);
							}
						}
					}
				}
			}

			UpdateComparisonView();
		}

		private void ResetDriftStatus(RunningStrategyInfo strategyInfo)
		{
			if (strategyInfo == null) return;
			
			var result = comparisonResults.FirstOrDefault(r => r.UniqueId == strategyInfo.UniqueId);
			if (result != null)
				result.IsAtRisk = false;
				
			strategyInfo.PausedByDrift = false;
		}
		
		private void LoadBacktestForStrategy(RunningStrategyInfo strategyInfo)
		{
			var trades = LoadTradesFileWithDialog("Select Backtest CSV for " + strategyInfo.Name);
			if (trades == null || !trades.Any()) return;

			UpdateBacktestData(strategyInfo, trades.Values.First());
		}

		private void LoadLiveForStrategy(RunningStrategyInfo strategyInfo)
		{
			var trades = LoadTradesFileWithDialog("Select Live CSV for " + strategyInfo.Name);
			if (trades == null || !trades.Any()) return;

			UpdateLiveData(strategyInfo, trades.Values.First());
		}

		private void PauseStrategy(RunningStrategyInfo strategyInfo, bool isAutoPause = false)
		{
			if (strategyInfo.Status != StrategyStatus.Running) return;
			
			if (strategyInfo.StrategyInstance != null)
			{
				strategyInfo.StrategyInstance.IsEnabled = false;
				
				string logMessage = isAutoPause 
					? $"[Monitor] Strategy {strategyInfo.Name} paused due to performance drift." 
					: $"Strategy '{strategyInfo.Name}' on '{strategyInfo.Instrument}' paused manually by Backtest Monitor.";
				Code.Output.Process(logMessage, PrintTo.OutputTab1);

				if(isAutoPause)
				{
					SystemSounds.Exclamation.Play();
					MessageBox.Show($"Strategy '{strategyInfo.Name}' on '{strategyInfo.Instrument}' has been automatically paused due to performance drift.", "Drift Alert", MessageBoxButton.OK, MessageBoxImage.Warning);
					try
					{
						var strategy = strategyInfo.StrategyInstance;
						var result = comparisonResults.FirstOrDefault(r => r.UniqueId == strategyInfo.UniqueId);
						if (strategy != null && result != null)
						{
							Code.Output.Process($"DRIFT ALERT: Strategy {strategy.Name} exceeded drift threshold on {DateTime.Now:MM/dd/yyyy}. Current PF: {result.LiveStats.ProfitFactor:F2}, Current Max DD: {result.LiveStats.MaxDrawdown:C}", PrintTo.OutputTab1);
							driftEvents.Add(new DriftEvent
							{
								StrategyName = strategy.Name,
								DetectionTime = DateTime.Now,
								ProfitFactor = result.LiveStats.ProfitFactor,
								MaxDrawdown = result.LiveStats.MaxDrawdown
							});
							
							((dynamic)strategy).DriftPauseAlert = true;
						}
					}
					catch(RuntimeBinderException)
					{
						MessageBox.Show("This strategy does not support visual drift alerts. Please add the following to your strategy class:\n\n" +
							"[NinjaScriptProperty]\n" +
							"[Browsable(false)]\n" +
							"public bool DriftPauseAlert { get; set; }\n\n" +
							"protected override void OnBarUpdate()\n" +
							"{\n" +
							"    if (DriftPauseAlert && State == State.Realtime)\n" +
							"    {\n" +
							"        Draw.VerticalLine(this, \"DriftPause-\" + CurrentBar, 0, Brushes.OrangeRed);\n" +
							"        DriftPauseAlert = false;\n" +
							"    }\n" +
							"}", "Visual Alert Not Supported", MessageBoxButton.OK, MessageBoxImage.Information);
					}
					catch(Exception ex)
					{
						Code.Output.Process($"[Monitor] Could not log drift event or trigger draw marker for {strategyInfo.Name}: {ex.Message}", PrintTo.OutputTab1);
					}
				}
			}
			
			strategyInfo.PausedByDrift = isAutoPause;
			strategyInfo.Status = StrategyStatus.Paused;
			UpdateComparisonView();
		}

		private void RestartStrategy(RunningStrategyInfo strategyInfo)
		{
			if(strategyInfo.Status != StrategyStatus.Paused) return;

			if (monitorSettings.RequireManualRestart && strategyInfo.PausedByDrift)
			{
				MessageBox.Show("Manual restart required. Please enable the strategy manually from the chart or click 'Reset Drift' to re-enable this button.");
				return;
			}
			
			if (strategyInfo.StrategyInstance != null)
			{
				strategyInfo.StrategyInstance.IsEnabled = true;
				Code.Output.Process($"Strategy '{strategyInfo.Name}' on '{strategyInfo.Instrument}' restarted by Backtest Monitor.", PrintTo.OutputTab1);
			}
			
			strategyInfo.PausedByDrift = false;
			strategyInfo.Status = StrategyStatus.Running;
			UpdateComparisonView();
		}
		#endregion

		#region Comparison Logic
		private void UpdateComparisonView()
		{
			foreach(var result in comparisonResults)
			{
				var runningInfo = runningStrategies.FirstOrDefault(s => s.UniqueId == result.UniqueId);
				result.Status = runningInfo?.Status ?? StrategyStatus.Unknown;

				result.LiveStats = CalculateStats(result.LiveTrades);
				result.BacktestStats = CalculateStats(result.BacktestTrades);
				
				var snapshot = new SlopeSnapshot
				{
					Timestamp = DateTime.Now,
					ProfitFactorSlope = result.ProfitFactorSlope,
					DrawdownSlope = result.DrawdownSlope,
					WinRateSlope = result.WinRateSlope
				};
				result.SlopeHistory.Add(snapshot);
				if(result.SlopeHistory.Count > 20) 
					result.SlopeHistory.RemoveAt(0);
				
				CheckForDriftRisk(result);
			}

			UpdateSummaryPanel();
			if (comparisonGrid != null)
				comparisonGrid.Items.Refresh();
		}

		private void CheckForDriftRisk(ComparisonResult result)
		{
			if (!monitorSettings.EnableAutoPause) return;

			var runningInfo = runningStrategies.FirstOrDefault(s => s.UniqueId == result.UniqueId);
			if (runningInfo == null || runningInfo.Status != StrategyStatus.Running) return;
			
			bool hasDrifted = result.LiveStats.ProfitFactor < monitorSettings.MinProfitFactorThreshold 
							  || result.LiveStats.MaxDrawdown > (result.BacktestStats.MaxDrawdown * monitorSettings.MaxDrawdownThresholdMultiplier);

			if (hasDrifted)
			{
				result.IsAtRisk = true;
				PauseStrategy(runningInfo, true);
			}
		}

		private void UpdateSummaryPanel()
		{
			if (summaryAtRiskText == null) return;

			int atRiskCount = comparisonResults.Count(r => r.IsAtRisk);
			double totalPnlDelta = comparisonResults.Sum(r => r.PnLDiff);
			double avgLivePf = comparisonResults.Count > 0 ? comparisonResults.Average(r => r.LiveStats.ProfitFactor) : 0;
			double avgBacktestPf = comparisonResults.Count > 0 ? comparisonResults.Average(r => r.BacktestStats.ProfitFactor) : 0;

			summaryAtRiskText.Text = $"At Risk: {atRiskCount}";
			summaryLivePfText.Text = $"Avg Live PF: {avgLivePf:F2}";
			summaryBacktestPfText.Text = $"Avg Backtest PF: {avgBacktestPf:F2}";
			summaryPnlDeltaText.Text = $"Total PnL Delta: {totalPnlDelta:C}";
		}

		private ComparisonStats CalculateStats(List<TradeRecord> trades)
		{
			if (trades == null || !trades.Any()) return new ComparisonStats();
			double grossProfit = trades.Where(t => t.PnL > 0).Sum(t => t.PnL);
			double grossLoss = Math.Abs(trades.Where(t => t.PnL < 0).Sum(t => t.PnL));
			double peakPnl = 0, maxDrawdown = 0, cumulativePnl = 0;
			foreach (var trade in trades)
			{
				cumulativePnl += trade.PnL;
				if (cumulativePnl > peakPnl) peakPnl = cumulativePnl;
				double drawdown = peakPnl - cumulativePnl;
				if (drawdown > maxDrawdown) maxDrawdown = drawdown;
			}
			return new ComparisonStats { PnL = cumulativePnl, WinRate = trades.Any() ? (double)trades.Count(t => t.PnL > 0) / trades.Count : 0, ProfitFactor = grossLoss > 0 ? grossProfit / grossLoss : double.PositiveInfinity, MaxDrawdown = maxDrawdown };
		}
		#endregion

		#region Data Loading and Helpers
		private void AutoLoadBacktestData(RunningStrategyInfo info, string filePath)
		{
			var trades = LoadTradesFileFromPath(filePath);
			if (trades != null && trades.Any())
				UpdateBacktestData(info, trades.Values.First());
		}

		private void AutoLoadLiveData(RunningStrategyInfo info, string filePath)
		{
			var trades = LoadTradesFileFromPath(filePath);
			if (trades != null && trades.Any())
				UpdateLiveData(info, trades.Values.First());
		}

		private void UpdateBacktestData(RunningStrategyInfo info, List<TradeRecord> trades)
		{
			var result = comparisonResults.FirstOrDefault(r => r.UniqueId == info.UniqueId);
			if (result == null)
			{
				result = new ComparisonResult { StrategyName = info.Name, Symbol = info.Instrument };
				comparisonResults.Add(result);
			}
			result.BacktestTrades = trades;
			info.IsBacktestLoaded = true;
			if(info.IsLiveLoaded) info.Status = info.StrategyInstance.IsEnabled ? StrategyStatus.Running : StrategyStatus.Paused;
			UpdateComparisonView();
		}

		private void UpdateLiveData(RunningStrategyInfo info, List<TradeRecord> trades)
		{
			var result = comparisonResults.FirstOrDefault(r => r.UniqueId == info.UniqueId);
			if (result == null)
			{
				result = new ComparisonResult { StrategyName = info.Name, Symbol = info.Instrument };
				comparisonResults.Add(result);
			}
			result.LiveTrades = trades;
			info.IsLiveLoaded = true;
			if(info.IsBacktestLoaded) info.Status = info.StrategyInstance.IsEnabled ? StrategyStatus.Running : StrategyStatus.Paused;

			if (trades.Any())
			{
				analysisStartDate = trades.Min(t => t.EntryTime.Date);
				analysisEndDate = trades.Max(t => t.EntryTime.Date);
				dateRangeLabel.Text = $"Analysis Period: {analysisStartDate:d} - {analysisEndDate:d}";
			}
			UpdateComparisonView();
		}
		#endregion

		#region Config, CSV, and LLM Methods
		private void ExportSummary()
		{
			string filePath = Path.Combine(logDirectory, "ComparisonExport.csv");
			try
			{
				var csv = new StringBuilder();
				csv.AppendLine("StrategyName,Instrument,LivePF,BacktestPF,PF_Delta,WinRate_Delta,DD_Delta,Status");

				foreach(var result in comparisonResults)
				{
					csv.AppendLine($"{result.StrategyName},{result.Symbol},{result.LiveStats.ProfitFactor:F2},{result.BacktestStats.ProfitFactor:F2},{result.ProfitFactorDiff:F2},{result.WinRateDiff:P1},{result.DrawdownDiff:C},{result.Status}");
				}
				
				File.WriteAllText(filePath, csv.ToString());
				MessageBox.Show($"Summary exported successfully to:\n{filePath}", "Export Successful", MessageBoxButton.OK, MessageBoxImage.Information);
			}
			catch (Exception ex)
			{
				MessageBox.Show($"Failed to export summary: {ex.Message}", "Export Error", MessageBoxButton.OK, MessageBoxImage.Error);
			}
		}
		
		private void SaveComparisonState()
		{
			string filePath = Path.Combine(logDirectory, "ComparisonSnapshot.json");
			try
			{
				var serializer = new JavaScriptSerializer();
				var json = serializer.Serialize(comparisonResults.ToList());
				File.WriteAllText(filePath, json);
				MessageBox.Show($"Comparison state saved to:\n{filePath}", "Save Successful", MessageBoxButton.OK, MessageBoxImage.Information);
			}
			catch (Exception ex)
			{
				MessageBox.Show($"Failed to save comparison state: {ex.Message}", "Save Error", MessageBoxButton.OK, MessageBoxImage.Error);
			}
		}

		private void LoadComparisonState()
		{
			string filePath = Path.Combine(logDirectory, "ComparisonSnapshot.json");
			if (!File.Exists(filePath))
			{
				MessageBox.Show($"Snapshot file not found at:\n{filePath}", "Load Error", MessageBoxButton.OK, MessageBoxImage.Error);
				return;
			}
			
			try
			{
				var serializer = new JavaScriptSerializer();
				var json = File.ReadAllText(filePath);
				var loadedResults = serializer.Deserialize<List<ComparisonResult>>(json);
				
				comparisonResults.Clear();
				foreach(var result in loadedResults)
					comparisonResults.Add(result);
				
				UpdateComparisonView();
				MessageBox.Show("Comparison state loaded successfully.", "Load Successful", MessageBoxButton.OK, MessageBoxImage.Information);
			}
			catch (Exception ex)
			{
				MessageBox.Show($"Failed to load comparison state: {ex.Message}", "Load Error", MessageBoxButton.OK, MessageBoxImage.Error);
			}
		}

		private void LoadAllConfigs()
		{
			LoadLlmConfig();
			LoadMonitorSettings();
		}

		private void SaveAllConfigs()
		{
			SaveLlmConfig();
			SaveMonitorSettings();
			MessageBox.Show("All settings saved.");
		}

		private void LoadMonitorSettings()
		{
			string path = Path.Combine(logDirectory, "MonitorSettings.json");
			if (!File.Exists(path)) return;
			try
			{
				string json = File.ReadAllText(path);
				Match autoPauseMatch = Regex.Match(json, "\"EnableAutoPause\":\\s*(true|false)", RegexOptions.IgnoreCase);
				if (autoPauseMatch.Success)
					monitorSettings.EnableAutoPause = bool.Parse(autoPauseMatch.Groups[1].Value);
				Match manualRestartMatch = Regex.Match(json, "\"RequireManualRestart\":\\s*(true|false)", RegexOptions.IgnoreCase);
				if (manualRestartMatch.Success)
					monitorSettings.RequireManualRestart = bool.Parse(manualRestartMatch.Groups[1].Value);
				if (autoPauseCheckBox != null) autoPauseCheckBox.IsChecked = monitorSettings.EnableAutoPause;
				if (manualRestartCheckBox != null) manualRestartCheckBox.IsChecked = monitorSettings.RequireManualRestart;
			}
			catch (Exception ex) { Code.Output.Process("Error loading monitor settings: " + ex.Message, PrintTo.OutputTab1); }
		}

		private void SaveMonitorSettings()
		{
			if (autoPauseCheckBox != null) monitorSettings.EnableAutoPause = autoPauseCheckBox.IsChecked ?? false;
			if (manualRestartCheckBox != null) monitorSettings.RequireManualRestart = manualRestartCheckBox.IsChecked ?? false;
			string path = Path.Combine(logDirectory, "MonitorSettings.json");
			try
			{
				string json = $"{{\"EnableAutoPause\": {monitorSettings.EnableAutoPause.ToString().ToLower()},\n \"RequireManualRestart\": {monitorSettings.RequireManualRestart.ToString().ToLower()}}}";
				File.WriteAllText(path, json);
			}
			catch (Exception ex) { Code.Output.Process("Error saving monitor settings: " + ex.Message, PrintTo.OutputTab1); }
		}

		private async Task ProcessUserQueryAsync() { await Task.Run(() => Dispatcher.Invoke(() => AppendToChatLog("User query processing not yet implemented.", Brushes.Red))); }
		private void AppendToChatLog(string message, Brush color) { Dispatcher.Invoke(() => { chatLogText.Inlines.Add(new Run(message) { Foreground = color, FontWeight=FontWeights.Bold }); chatLogText.Inlines.Add(new LineBreak()); if (chatLogText.Parent is ScrollViewer sv) { sv.ScrollToEnd(); } }); }
		private UIElement BuildLlmConfigPanel() { var llmExpander = new Expander { Header = "LLM Settings", IsExpanded = false, BorderBrush = Brushes.Gray, BorderThickness = new Thickness(1), Margin = new Thickness(5), Padding = new Thickness(5) }; var settingsGrid = new Grid(); for (int i = 0; i < 6; i++) settingsGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto }); settingsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto }); settingsGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) }); settingsGrid.Children.Add(new TextBlock { Text = "Provider:", Margin = new Thickness(5), VerticalAlignment = VerticalAlignment.Center }); providerComboBox = new ComboBox { Items = { "OpenRouter", "Google Gemini" }, Margin = new Thickness(5) }; Grid.SetRow(providerComboBox, 0); Grid.SetColumn(providerComboBox, 1); settingsGrid.Children.Add(providerComboBox); settingsGrid.Children.Add(new TextBlock { Text = "API Key:", Margin = new Thickness(5), VerticalAlignment = VerticalAlignment.Center }); apiKeyBox = new PasswordBox { Margin = new Thickness(5) }; Grid.SetRow(apiKeyBox, 1); Grid.SetColumn(apiKeyBox, 1); settingsGrid.Children.Add(apiKeyBox); settingsGrid.Children.Add(new TextBlock { Text = "Model:", Margin = new Thickness(5), VerticalAlignment = VerticalAlignment.Center }); modelComboBox = new ComboBox { Margin = new Thickness(5) }; Grid.SetRow(modelComboBox, 3); Grid.SetColumn(modelComboBox, 1); settingsGrid.Children.Add(modelComboBox); var saveButton = new Button { Content = "Save LLM Settings", Margin = new Thickness(5) }; saveButton.Click += (s, e) => SaveLlmConfig(); Grid.SetRow(saveButton, 4); Grid.SetColumnSpan(saveButton, 2); settingsGrid.Children.Add(saveButton); llmStatusText = new TextBlock { Text = "Ready.", Margin = new Thickness(5), TextWrapping = TextWrapping.Wrap }; Grid.SetRow(llmStatusText, 5); Grid.SetColumnSpan(llmStatusText, 2); settingsGrid.Children.Add(llmStatusText); llmExpander.Content = settingsGrid; return llmExpander; }
		private void LoadLlmConfig() { string configPath = Path.Combine(logDirectory, "LlmConfig.json"); if (!File.Exists(configPath)) return; try { string json = File.ReadAllText(configPath); llmConfig.Provider = Regex.Match(json, "\"Provider\":\\s*\"(.*?)\"").Groups[1].Value; llmConfig.ApiKey = Regex.Match(json, "\"ApiKey\":\\s*\"(.*?)\"").Groups[1].Value; llmConfig.SelectedModel = Regex.Match(json, "\"SelectedModel\":\\s*\"(.*?)\"").Groups[1].Value; providerComboBox.SelectedItem = llmConfig.Provider; apiKeyBox.Password = llmConfig.ApiKey; if (!string.IsNullOrEmpty(llmConfig.SelectedModel) && !modelComboBox.Items.Contains(llmConfig.SelectedModel)) modelComboBox.Items.Add(llmConfig.SelectedModel); modelComboBox.SelectedItem = llmConfig.SelectedModel; llmStatusText.Text = "LLM Config loaded."; } catch { llmStatusText.Text = "Error loading LLM config."; } }
		private void SaveLlmConfig() { llmConfig.Provider = providerComboBox.SelectedItem as string; llmConfig.ApiKey = apiKeyBox.Password; llmConfig.SelectedModel = modelComboBox.SelectedItem as string; string configPath = Path.Combine(logDirectory, "LlmConfig.json"); try { string json = $"{{\"Provider\": \"{llmConfig.Provider}\", \"ApiKey\": \"{llmConfig.ApiKey}\", \"SelectedModel\": \"{llmConfig.SelectedModel}\"}}"; File.WriteAllText(configPath, json); llmStatusText.Text = "LLM Settings saved!"; } catch (Exception ex) { llmStatusText.Text = $"Error saving LLM config: {ex.Message}"; } }
		private void LoadChatHistory() { string chatHistoryPath = Path.Combine(logDirectory, "ChatHistory.txt"); if (!File.Exists(chatHistoryPath)) return; try { var lines = File.ReadAllLines(chatHistoryPath); foreach (var line in lines) { if (line.StartsWith("User: ")) chatHistory.Add(new ChatMessage { Role = "User", Content = line.Substring(6) }); else if (line.StartsWith("AI: ")) chatHistory.Add(new ChatMessage { Role = "AI", Content = line.Substring(4) }); } foreach (var msg in chatHistory) { AppendToChatLog(msg.Role == "User" ? $"User: {msg.Content}" : $"AI: {msg.Content}", msg.Role == "User" ? Brushes.Blue : Brushes.Green); } } catch { /* ignore */ } }
		private void SaveChatHistory() { string chatHistoryPath = Path.Combine(logDirectory, "ChatHistory.txt"); try { File.WriteAllLines(chatHistoryPath, chatHistory.Select(msg => $"{msg.Role}: {msg.Content}")); } catch { /* ignore */ } }

		private Dictionary<string, List<TradeRecord>> LoadTradesFileWithDialog(string dialogTitle)
		{
			var dialog = new OpenFileDialog { Filter = "CSV Files (*.csv)|*.csv", Title = dialogTitle };
			if (dialog.ShowDialog() != true) return null;

			var trades = LoadTradesFileFromPath(dialog.FileName);
			if(trades != null)
				MessageBox.Show($"Loaded {trades.Values.Sum(list => list.Count)} trades for {trades.Count} pairs.");

			return trades;
		}

		private Dictionary<string, List<TradeRecord>> LoadTradesFileFromPath(string filePath)
		{
			var tradesByStrategyAndSymbol = new Dictionary<string, List<TradeRecord>>();
			try
			{
				using (var reader = new StreamReader(filePath))
				{
					string headerLine = reader.ReadLine();
					if (string.IsNullOrEmpty(headerLine)) throw new Exception("CSV empty.");
					string[] headers = headerLine.Split(',').Select(h => h.Trim()).ToArray();
					int entryTimeIndex = Array.IndexOf(headers, "Entry time"), exitTimeIndex = Array.IndexOf(headers, "Exit time"), pnlIndex = Array.IndexOf(headers, "Profit"), symbolIndex = Array.IndexOf(headers, "Instrument"), strategyIndex = Array.IndexOf(headers, "Strategy");
					if (new[] { entryTimeIndex, exitTimeIndex, pnlIndex, symbolIndex, strategyIndex }.Any(i => i == -1)) throw new Exception("Could not find all required CSV columns (Entry time, Exit time, Profit, Instrument, Strategy).");
					while (!reader.EndOfStream)
					{
						var line = reader.ReadLine(); if (string.IsNullOrWhiteSpace(line)) continue;
						string[] parts = line.Split(',');
						try
						{
							string strategyName = parts[strategyIndex].Trim();
							string symbol = parts[symbolIndex].Trim();
							string compositeKey = $"{strategyName}_{symbol}";
							tradesByStrategyAndSymbol.GetOrAdd(compositeKey).Add(new TradeRecord { EntryTime = DateTime.ParseExact(parts[entryTimeIndex].Trim(), "M/d/yyyy h:mm:ss tt", CultureInfo.InvariantCulture), ExitTime = DateTime.ParseExact(parts[exitTimeIndex].Trim(), "M/d/yyyy h:mm:ss tt", CultureInfo.InvariantCulture), PnL = ParseCurrency(parts[pnlIndex].Trim()), Symbol = symbol, StrategyName = strategyName });
						}
						catch (Exception ex) { NinjaTrader.Code.Output.Process($"Error parsing trade line: '{line}' | {ex.Message}", PrintTo.OutputTab1); }
					}
				}
				return tradesByStrategyAndSymbol;
			}
			catch (Exception ex)
			{
				MessageBox.Show($"Error reading trades CSV from '{filePath}': " + ex.Message);
				return null;
			}
		}

		private double ParseCurrency(string input) { if (string.IsNullOrEmpty(input)) return 0; string clean = input.Trim().Replace("$", "").Replace(",", "").Replace("(", "-").Replace(")", ""); if (double.TryParse(clean, NumberStyles.Any, CultureInfo.InvariantCulture, out double result)) return result; return 0; }
		#endregion
	}

	#region Data Models
	public class RunningStrategyInfo : INotifyPropertyChanged
	{
		private StrategyStatus _status;
		private bool _isBacktestLoaded, _isLiveLoaded;
		private bool _pausedByDrift;

		public string Name { get; set; }
		public string Instrument { get; set; }
		public string Account { get; set; }
		[ScriptIgnore] public Strategy StrategyInstance { get; set; }
		public string UniqueId => $"{Name}_{Instrument.Replace(" ", "")}";

		public bool PausedByDrift 
		{ 
			get => _pausedByDrift;
			set 
			{
				if (_pausedByDrift == value) return;
				_pausedByDrift = value;
				OnPropertyChanged(nameof(PausedByDrift));
				OnPropertyChanged(nameof(CanResetDrift));
			}
		}

		public StrategyStatus Status { get => _status; set { _status = value; OnPropertyChanged(nameof(Status)); OnPropertyChanged(nameof(CanPause)); OnPropertyChanged(nameof(CanRestart)); } }
		public bool IsBacktestLoaded { get => _isBacktestLoaded; set { _isBacktestLoaded = value; OnPropertyChanged(nameof(IsBacktestLoaded)); } }
		public bool IsLiveLoaded { get => _isLiveLoaded; set { _isLiveLoaded = value; OnPropertyChanged(nameof(IsLiveLoaded)); } }
		public bool CanPause => Status == StrategyStatus.Running;
		public bool CanRestart => Status == StrategyStatus.Paused;
		public bool CanResetDrift => PausedByDrift;
		public event PropertyChangedEventHandler PropertyChanged;
		protected void OnPropertyChanged(string name) { PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name)); }
	}

	public class ComparisonResult : INotifyPropertyChanged
	{
		private bool _isAtRisk;
		private StrategyStatus _status;
		public string StrategyName { get; set; }
		public string Symbol { get; set; }
		public string UniqueId => $"{StrategyName}_{Symbol.Replace(" ", "")}";
		public StrategyStatus Status { get => _status; set { _status = value; OnPropertyChanged(nameof(Status)); } }
		[ScriptIgnore] public List<TradeRecord> BacktestTrades { get; set; } = new List<TradeRecord>();
		[ScriptIgnore] public List<TradeRecord> LiveTrades { get; set; } = new List<TradeRecord>();
		public ComparisonStats BacktestStats { get; set; } = new ComparisonStats();
		public ComparisonStats LiveStats { get; set; } = new ComparisonStats();
		public double PnLDiff => LiveStats.PnL - BacktestStats.PnL;
		public double ProfitFactorDiff => (BacktestStats.ProfitFactor == double.PositiveInfinity || LiveStats.ProfitFactor == double.PositiveInfinity) ? 0 : LiveStats.ProfitFactor - BacktestStats.ProfitFactor;
		public double WinRateDiff => LiveStats.WinRate - BacktestStats.WinRate;
		public double DrawdownDiff => LiveStats.MaxDrawdown - BacktestStats.MaxDrawdown;
		public double ProfitFactorSlope { get; set; }
		public double DrawdownSlope { get; set; }
		public double WinRateSlope { get; set; }
		[ScriptIgnore] public List<SlopeSnapshot> SlopeHistory { get; set; } = new List<SlopeSnapshot>();
		public bool IsAtRisk { get => _isAtRisk; set { _isAtRisk = value; OnPropertyChanged(nameof(IsAtRisk)); } }
		public event PropertyChangedEventHandler PropertyChanged;
		protected void OnPropertyChanged(string name) { PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name)); }
	}

	public class MonitorSettings 
	{ 
		public bool EnableAutoPause { get; set; } = true; 
		public bool RequireManualRestart { get; set; } = true; 
		public double MinProfitFactorThreshold { get; set; } = 0.8;
		public double MaxDrawdownThresholdMultiplier { get; set; } = 2.0;
	}
	public class TradeRecord { public DateTime EntryTime { get; set; } public DateTime ExitTime { get; set; } public double PnL { get; set; } public string Symbol { get; set; } public string StrategyName { get; set; } }
	public class ComparisonStats { public double PnL { get; set; } public double WinRate { get; set; } public double ProfitFactor { get; set; } public double MaxDrawdown { get; set; } }
	public class LlmConfig { public string Provider { get; set; } public string ApiKey { get; set; } public string SelectedModel { get; set; } }
	public class ChatMessage { public string Role { get; set; } public string Content { get; set; } }
	public class DriftEvent
	{
		public string StrategyName { get; set; }
		public DateTime DetectionTime { get; set; }
		public double ProfitFactor { get; set; }
		public double MaxDrawdown { get; set; }
	}
	public class SlopeSnapshot
	{
		public DateTime Timestamp { get; set; }
		public double ProfitFactorSlope { get; set; }
		public double DrawdownSlope { get; set; }
		public double WinRateSlope { get; set; }
	}
	#endregion

	#region Value Converters and Extensions
	public static class DictionaryExtensions
	{
		public static List<T> GetOrAdd<K, T>(this Dictionary<K, List<T>> dict, K key)
		{
			if (!dict.ContainsKey(key)) dict[key] = new List<T>();
			return dict[key];
		}
	}

	public class GreaterThanConverter : IValueConverter
	{
		public object Convert(object value, Type targetType, object parameter, CultureInfo culture) { double val = System.Convert.ToDouble(value); double limit = System.Convert.ToDouble(parameter); return val > limit; }
		public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotImplementedException();
	}

	public class LessThanConverter : IValueConverter
	{
		public object Convert(object value, Type targetType, object parameter, CultureInfo culture) { double val = System.Convert.ToDouble(value); double limit = System.Convert.ToDouble(parameter); return val < limit; }
		public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotImplementedException();
	}

	public class SlopeToArrowConverter : IValueConverter
	{
		public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
		{
			double val = System.Convert.ToDouble(value);
			bool invert = parameter != null && System.Convert.ToBoolean(parameter);
			if (val > 0.001) return invert ? "▼" : "▲";
			if (val < -0.001) return invert ? "▲" : "▼";
			return "●";
		}
		public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) => throw new NotImplementedException();
	}
	
	public class HistoryToTrendConverter : IMultiValueConverter
	{
		public object Convert(object[] values, Type targetType, object parameter, CultureInfo culture)
		{
			if (values == null || values.Length < 3 || values.Any(v => v == DependencyProperty.UnsetValue) || !(values[0] is double) || !(values[1] is List<SlopeSnapshot> history) || !(values[2] is string propName))
				return "History unavailable";

			double currentSlope = (double)values[0];
			string trendArrow = "●"; // Flat
			if (history.Count > 1)
			{
				double first = GetSlopeValue(history.First(), propName);
				double last = GetSlopeValue(history.Last(), propName);
				if (last > first) trendArrow = "▲"; // Increasing
				else if (last < first) trendArrow = "▼"; // Decreasing
			}
			
			string historyText = string.Join(", ", history.Select(h => GetSlopeValue(h, propName).ToString("F2")));
			return $"Slope: {currentSlope:F2}\nTrend: {trendArrow}\nHistory: [{historyText}]";
		}

		private double GetSlopeValue(SlopeSnapshot snapshot, string propName)
		{
			switch(propName)
			{
				case "ProfitFactorSlope": return snapshot.ProfitFactorSlope;
				case "WinRateSlope": return snapshot.WinRateSlope;
				case "DrawdownSlope": return snapshot.DrawdownSlope;
				default: return 0;
			}
		}

		public object[] ConvertBack(object value, Type[] targetTypes, object parameter, CultureInfo culture)
		{
			throw new NotImplementedException();
		}
	}

	public class BooleanToVisibilityConverter : IValueConverter
	{
		public object Convert(object value, Type targetType, object parameter, CultureInfo culture) { return (value is bool && (bool)value) ? Visibility.Visible : Visibility.Collapsed; }
		public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) { return value is Visibility && (Visibility)value == Visibility.Visible; }
	}

	public class InverseBooleanToVisibilityConverter : IValueConverter
	{
		public object Convert(object value, Type targetType, object parameter, CultureInfo culture) { return (value is bool && (bool)value) ? Visibility.Collapsed : Visibility.Visible; }
		public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture) { return value is Visibility && (Visibility)value == Visibility.Collapsed; }
	}
	#endregion
}
