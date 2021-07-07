import { Component, createRef, h } from "preact";
import * as d3 from "d3";

export const colours = {
  easy: "rgb(30, 142, 62)",
  hard: "rgb(237, 69, 40)",
  tricky: "rgb(237, 170, 30)",
  peer: "rgb(25, 118, 188)",
};

export class PlotConfusionMatrix extends Component {
  state = {
    matrix: {},
  };

  ref = createRef();

  shouldComponentUpdate(nextProps, nextState) {
    if (nextProps.plot == true) {
      const freq = this.props.freq;
      this.state.matrix["easy"] = this.props._matrix["easy"]
        ? this.props._matrix["easy"]
        : 0;
      this.state.matrix["hard"] = this.props._matrix["hard"]
        ? this.props._matrix["hard"]
        : 0;
      this.state.matrix["tricky"] = this.props._matrix["tricky"]
        ? this.props._matrix["tricky"]
        : 0;
      this.state.matrix["peer"] = this.props._matrix["peer"]
        ? this.props._matrix["peer"]
        : 0;

      const matrixSvg = d3.select(this.ref.current).select("#matrix");

      matrixSvg.selectAll("*").remove();

      let size = +matrixSvg.attr("width");
      const g = matrixSvg.append("g");
      g.append("text")
        .attr("class", "legend")
        .attr("x", size / 2)
        .attr("y", -6)
        .style("font-size", "7pt")
        .attr("text-anchor", "middle")
        .style("opacity", 0)
        .text();

      const easy = g
        .append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", size / 2)
        .attr("height", size / 2)
        .attr("fill", colours["easy"])
        .style("opacity", 0.5 + 0.5 * this.state.matrix["easy"]);

      easy.on("mousemove", () => {
        g.select(".legend")
          .style("opacity", 1)
          .style("fill", colours["easy"])
          .text("Right > Right");
      });
      easy.on("mouseout", () => {
        g.select(".legend").transition().duration(100).style("opacity", 0);
      });

      g.append("text")
        .attr("x", size / 4)
        .attr("y", size / 4)
        .attr("dy", 4)
        .style("font-size", "8pt")
        .style("fill", "white")
        .style("text-anchor", "middle")
        .attr("pointer-events", "none")
        .text(`${parseInt(100 * this.state.matrix["easy"])}%`);

      const hard = g
        .append("rect")
        .attr("x", size / 2)
        .attr("y", size / 2)
        .attr("width", size / 2)
        .attr("height", size / 2)
        .attr("fill", colours["hard"])
        .style("opacity", 0.5 + 0.5 * this.state.matrix["hard"]);

      hard.on("mousemove", () => {
        g.select(".legend")
          .style("opacity", 1)
          .style("fill", colours["hard"])
          .text("Wrong > Wrong");
      });
      hard.on("mouseout", () => {
        g.select(".legend").transition().duration(100).style("opacity", 0);
      });

      g.append("text")
        .attr("x", (3 * size) / 4)
        .attr("y", (3 * size) / 4)
        .attr("dy", 4)
        .style("font-size", "8pt")
        .style("fill", "white")
        .style("text-anchor", "middle")
        .attr("pointer-events", "none")
        .text(`${parseInt(100 * this.state.matrix["hard"])}%`);

      const peer = g
        .append("rect")
        .attr("x", 0)
        .attr("y", size / 2)
        .attr("width", size / 2)
        .attr("height", size / 2)
        .attr("fill", colours["peer"])
        .style("opacity", 0.5 + 0.5 * this.state.matrix["peer"]);

      peer.on("mousemove", () => {
        g.select(".legend")
          .style("opacity", 1)
          .style("fill", colours["peer"])
          .text("Wrong > Right");
      });
      peer.on("mouseout", () => {
        g.select(".legend").transition().duration(100).style("opacity", 0);
      });

      g.append("text")
        .attr("x", size / 4)
        .attr("y", (3 * size) / 4)
        .attr("dy", 4)
        .style("font-size", "8pt")
        .style("fill", "white")
        .style("text-anchor", "middle")
        .attr("pointer-events", "none")
        .text(`${parseInt(100 * this.state.matrix["peer"])}%`);

      const tricky = g
        .append("rect")
        .attr("x", size / 2)
        .attr("y", 0)
        .attr("width", size / 2)
        .attr("height", size / 2)
        .attr("fill", colours["tricky"])
        .style("opacity", 0.5 + 0.5 * this.state.matrix["tricky"]);

      tricky.on("mousemove", () => {
        g.select(".legend")
          .style("opacity", 1)
          .style("fill", colours["tricky"])
          .text("Right > Wrong");
      });
      tricky.on("mouseout", () => {
        g.select(".legend").transition().duration(100).style("opacity", 0);
      });

      g.append("text")
        .attr("x", (3 * size) / 4)
        .attr("y", size / 4)
        .attr("dy", 4)
        .style("font-size", "8pt")
        .style("fill", "white")
        .style("text-anchor", "middle")
        .attr("pointer-events", "none")
        .text(`${parseInt(100 * this.state.matrix["tricky"])}%`);

      const firstFreqSvg = d3
        .select(this.ref.current)
        .select("#first-frequency");

      firstFreqSvg.selectAll("*").remove();

      const secondFreqSvg = d3
        .select(this.ref.current)
        .select("#second-frequency");

      secondFreqSvg.selectAll("*").remove();

      const margin = { left: 30, right: 30 };

      let sum = 0;
      for (const entry in freq["first_choice"]) {
        if ({}.hasOwnProperty.call(freq["first_choice"], entry)) {
          sum += freq["first_choice"][entry];
        }
      }
      for (const entry in freq["first_choice"]) {
        if ({}.hasOwnProperty.call(freq["first_choice"], entry)) {
          freq["first_choice"][entry] /= sum;
          freq["second_choice"][entry] /= sum;
        }
      }

      size = +secondFreqSvg.attr("width") - margin.left;

      const x = d3.scaleLinear().domain([0, 1]).rangeRound([0, size]);
      const y = d3
        .scaleBand()
        .domain(d3.keys(freq["first_choice"]).sort())
        .rangeRound([0, firstFreqSvg.attr("height")]);

      const gg = secondFreqSvg
        .append("g")
        .attr("transform", `translate(${margin.left},0)`);

      const ggg = firstFreqSvg.append("g");

      gg.append("g")
        .attr("class", "axis axis--x")
        .style("opacity", 0)
        .call(d3.axisBottom(x));

      ggg
        .append("g")
        .attr("class", "axis axis--x")
        .style("opacity", 0)
        .call(d3.axisBottom(x));

      gg.append("g")
        .attr("class", "axis axis--y")
        .style("opacity", 0)
        .call(d3.axisLeft(y).ticks);

      gg.append("g")
        .selectAll("rect")
        .data(d3.entries(freq["second_choice"]))
        .enter()
        .append("rect")
        .attr("finalwidth", function (d) {
          return x(d.value);
        })
        .attr("x", x(0))
        .attr("y", function (d) {
          return y(d.key);
        })
        .attr("width", function (d) {
          return x(d.value);
        })
        .attr(
          "height",
          firstFreqSvg.attr("height") /
            d3.values(freq["second_choice"]).length,
        )
        .attr("fill", "gray")
        .style("stroke", "white")
        .style("opacity", 0.2);

      ggg
        .append("g")
        .selectAll("rect")
        .data(d3.entries(freq["first_choice"]))
        .enter()
        .append("rect")
        .attr("finalwidth", function (d) {
          return x(d.value);
        })
        .attr("finalx", function (d) {
          return x(1 - d.value);
        })
        .attr("x", function (d) {
          return x(1 - d.value);
        })
        .attr("y", function (d) {
          return y(d.key);
        })
        .attr("width", function (d) {
          return x(d.value);
        })
        .attr(
          "height",
          firstFreqSvg.attr("height") / d3.values(freq["first_choice"]).length,
        )
        .attr("fill", "gray")
        .style("stroke", "white")
        .style("opacity", 0.2);

      gg.append("g")
        .selectAll("text")
        .data(d3.entries(freq["second_choice"]))
        .enter()
        .append("text")
        .attr("x", x(0))
        .attr("dx", -2)
        .attr("y", function (d) {
          return y(d.key);
        })
        .attr("dy", y.bandwidth() / 2 + 4)
        .style("font-size", "8pt")
        .style("text-anchor", "end")
        .text(function (d) {
          return `${parseInt(100 * d.value)}%`;
        });

      ggg
        .append("g")
        .selectAll("text")
        .data(d3.entries(freq["first_choice"]))
        .enter()
        .append("text")
        .attr("x", x(1))
        .attr("dx", 2)
        .attr("y", function (d) {
          return y(d.key);
        })
        .attr("dy", y.bandwidth() / 2 + 4)
        .style("font-size", "8pt")
        .style("text-anchor", "start")
        .text(function (d) {
          return `${parseInt(100 * d.value)}%`;
        });

      gg.append("g")
        .selectAll("text")
        .data(d3.entries(freq["second_choice"]))
        .enter()
        .append("text")
        .attr("x", x(0))
        .attr("dx", 2)
        .attr("y", function (d) {
          return y(d.key);
        })
        .attr("dy", y.bandwidth() / 2 + 4)
        .style("font-size", "8pt")
        .text(function (d) {
          return d.key;
        });
    }
  }

  render() {
    return (
      <div style={{ overflow: "visible" }} ref={this.ref}>
        <svg
          id="first-frequency"
          width="200"
          height="80"
          className="vertical-align"
        />
        <svg id="matrix" width="60" height="60" className="vertical-align" />
        <svg
          id="second-frequency"
          width="200"
          height="80"
          className="vertical-align"
        />
      </div>
    );
  }
}
